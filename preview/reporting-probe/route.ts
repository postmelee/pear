// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import { env } from "cloudflare:workers";
export const dynamic = "force-dynamic";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const reply = (data: unknown, status = 200) => Response.json(data, { status,
  headers: { "Cache-Control": "no-store", "Referrer-Policy": "no-referrer" } });
async function digest(value: string) {
  return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value))))
    .map(v => v.toString(16).padStart(2, "0")).join("");
}
// Public synthetic experiment only. No list/admin route or player data.
async function handle(request: Request) {
  const db = env.DB!;
  const now = Math.floor(Date.now() / 1000), bucket = Math.floor(now / 60);
  const rate = await db.prepare(`INSERT INTO probe_limits (bucket, count) VALUES (?, 1)
    ON CONFLICT(bucket) DO UPDATE SET count = count + 1 WHERE count < 120 RETURNING count`)
    .bind(bucket).first();
  if (!rate) return reply({error: "rate limited"}, 429);
  await db.batch([
    db.prepare("DELETE FROM probe_limits WHERE bucket < ?").bind(bucket - 1),
    db.prepare("DELETE FROM capability_probes WHERE expires < ?").bind(now)
  ]);
  const id = new URL(request.url).searchParams.get("id") || "";
  const token = request.headers.get("Authorization")?.match(/^Bearer ([0-9a-f]{64})$/)?.[1];
  if (!uuid.test(id) || !token) return reply({error: "report capability required"}, 401);
  const owner = await digest(token);
  const existing = await db.prepare("SELECT * FROM capability_probes WHERE id = ?").bind(id).first();
  if (existing && existing.owner !== owner) return reply({error: "not found"}, 404);
  if (request.method === "GET") {
    if (!existing || existing.deleted) return reply({error: "not found"}, 404);
    return reply({id, revision: existing.revision, value: existing.value});
  }
  if (request.method === "DELETE") {
    if (!existing) return reply({error: "not found"}, 404);
    await db.prepare("UPDATE capability_probes SET deleted = 1, value = NULL WHERE id = ? AND owner = ?")
      .bind(id, owner).run();
    return reply({deleted: true});
  }
  if (existing?.deleted) return reply({error: "deleted"}, 410);
  if (request.headers.get("Content-Type")?.split(";")[0] !== "application/json") return reply({error:"JSON required"},415);
  const reader = request.body?.getReader();
  if (!reader) return reply({error:"body required"},400);
  let bytes = new Uint8Array(0);
  while (true) {
    const {done,value} = await reader.read();
    if (done) break;
    if (bytes.length + value.length > 512) { await reader.cancel(); return reply({error:"too large"},413); }
    const next = new Uint8Array(bytes.length + value.length); next.set(bytes); next.set(value,bytes.length); bytes=next;
  }
  let input;
  try { input = JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes)); }
  catch { return reply({error:"invalid JSON"},400); }
  if (!input || Object.keys(input).sort().join(",") !== "fixture,requestID,revision,value" ||
      input.fixture !== "pear-synthetic" || !uuid.test(input.requestID) ||
      !Number.isSafeInteger(input.revision) || input.revision < 1 || input.revision > 100 ||
      ![1,2].includes(input.value)) return reply({error:"synthetic fixture only"},400);
  if (existing && existing.revision === input.revision && existing.request_id === input.requestID && existing.value === input.value)
    return reply({id, revision:existing.revision, value:existing.value});
  // Atomic revision/owner predicate prevents concurrent overwrite.
  const changed = await db.prepare(`INSERT INTO capability_probes
    (id, owner, revision, request_id, value, deleted, expires)
    SELECT ?, ?, ?, ?, ?, 0, ? WHERE ? = 1 AND (SELECT COUNT(*) FROM capability_probes) < 64
    ON CONFLICT(id) DO UPDATE SET revision = excluded.revision, request_id = excluded.request_id, value = excluded.value
    WHERE capability_probes.owner = excluded.owner AND capability_probes.deleted = 0
      AND capability_probes.revision = excluded.revision - 1 RETURNING revision`)
    .bind(id,owner,input.revision,input.requestID,input.value,now+86400,existing ? 1 : input.revision).first();
  if (!changed) return reply({error:"revision conflict or experiment capacity reached"},409);
  return reply({id,revision:input.revision,value:input.value});
}
export const GET = handle;
export const PUT = handle;
export const DELETE = handle;

/* Original Pear SDK dependency fixture. Compile/link only; do not execute.
 * Retained typed addresses require real framework symbols without calling them.
 * Carbon/OpenGL are intentional dependencies of the selected Wine Mac driver.
 */
#import <AppKit/AppKit.h>
#import <Carbon/Carbon.h>
#import <Foundation/Foundation.h>
#import <IOKit/IOKitLib.h>
#import <Metal/Metal.h>
#import <OpenGL/OpenGL.h>
#import <QuartzCore/QuartzCore.h>
#import <Security/Security.h>
#import <CoreText/CoreText.h>
#import <ApplicationServices/ApplicationServices.h>
#import <CoreFoundation/CoreFoundation.h>
#import <CoreServices/CoreServices.h>
#import <DiskArbitration/DiskArbitration.h>
#import <SystemConfiguration/SystemConfiguration.h>

#if !defined(__APPLE__) || !defined(__aarch64__)
#error This fixture requires native ARM64 macOS compilation.
#endif

#define PEAR_REFERENCE(name, symbol) \
    static __typeof__(&(symbol)) const name __attribute__((used)) = &(symbol)

PEAR_REFERENCE(appkit_reference, NSApplicationMain);
PEAR_REFERENCE(carbon_reference, GetCurrentProcess);
PEAR_REFERENCE(foundation_reference, NSGetSizeAndAlignment);
PEAR_REFERENCE(iokit_reference, IOServiceMatching);
PEAR_REFERENCE(metal_reference, MTLCreateSystemDefaultDevice);
PEAR_REFERENCE(opengl_reference, CGLChoosePixelFormat);
PEAR_REFERENCE(quartzcore_reference, CACurrentMediaTime);
PEAR_REFERENCE(security_reference, SecRandomCopyBytes);
PEAR_REFERENCE(coretext_reference, CTFontCreateWithName);
PEAR_REFERENCE(applicationservices_reference, CGMainDisplayID);
PEAR_REFERENCE(corefoundation_reference, CFGetTypeID);
PEAR_REFERENCE(coreservices_reference, UTTypeConformsTo);
PEAR_REFERENCE(diskarbitration_reference, DASessionCreate);
PEAR_REFERENCE(systemconfiguration_reference, SCPreferencesCreate);

int main(void)
{
    return 0;
}

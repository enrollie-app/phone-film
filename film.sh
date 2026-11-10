#!/bin/bash
# Boots one simulated iPhone, opens the public install page in Safari, and runs a filming script against it.
set -uo pipefail
export OUT="$PWD/out"
mkdir -p "$OUT"
sudo xcode-select -s "$XCODE"
xcodebuild -version | tr '\n' ' '; echo
brew install cameroncooke/axe/axe >/dev/null 2>&1 || brew install axe >/dev/null 2>&1
axe --version
axe tap --help > "$OUT/axe-tap-help.txt" 2>&1
axe swipe --help > "$OUT/axe-swipe-help.txt" 2>&1
axe touch --help > "$OUT/axe-touch-help.txt" 2>&1

export U
U="$(xcrun simctl create film "com.apple.CoreSimulator.SimDeviceType.$PHONE" "com.apple.CoreSimulator.SimRuntime.$RUNTIME")"
echo "device $U"
xcrun simctl boot "$U"
xcrun simctl bootstatus "$U" -b | tail -1
export FILM_LANG="${FILM_LANG:-en}"
HOOK_FLAG=""
# No first-time keyboard popup on the Add screen.
for domain in com.apple.Preferences com.apple.keyboard.ContinuousPath; do
  xcrun simctl spawn "$U" defaults write "$domain" DidShowContinuousPathIntroduction -bool true
done
xcrun simctl spawn "$U" defaults write com.apple.Preferences KeyboardDidShowProductivityTutorial -bool true
xcrun simctl spawn "$U" defaults write com.apple.Preferences DidShowGestureKeyboardIntroduction -bool true
if [ "$FILM_LANG" = es ]; then
  xcrun simctl spawn "$U" defaults write -g AppleLanguages -array es-MX es
  xcrun simctl spawn "$U" defaults write -g AppleLocale -string es_MX
  HOOK_FLAG="-DFILM_ES=1"
fi
xcrun simctl shutdown "$U"
xcrun simctl boot "$U"
xcrun simctl bootstatus "$U" -b | tail -1
xcrun simctl status_bar "$U" override --time 9:41 --dataNetwork wifi --wifiMode active --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState charged --batteryLevel 100

SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
xcrun clang -arch arm64 -isysroot "$SDK" -target "arm64-apple-ios$TARGET-simulator" -dynamiclib -fobjc-arc $HOOK_FLAG \
  -framework Foundation -framework WebKit hook/filmhook.m -o hook/filmhook.dylib
export HOOK="$PWD/hook/filmhook.dylib"

xcrun simctl io "$U" recordVideo --codec=h264 --force "$OUT/take.mov" >/dev/null 2>&1 &
REC=$!
sleep 2
SIMCTL_CHILD_DYLD_INSERT_LIBRARIES="$HOOK" xcrun simctl launch --terminate-running-process "$U" com.apple.mobilesafari
sleep 6
python3 -I "$SCRIPT" 2>&1 | tee "$OUT/log.txt"
RESULT=${PIPESTATUS[0]}
kill -INT "$REC"
wait "$REC"
xcrun simctl spawn "$U" log show --last 2m --predicate 'eventMessage CONTAINS "filmhook"' 2>/dev/null | tail -3
ls -la "$OUT" | cut -c30- | head -40
exit "$RESULT"

cmake_minimum_required(VERSION 3.22)

if(APPLE)
    # Apple Silicon (M1/M2/M3) native build. Pass -DPSXL_UNIVERSAL=ON for arm64 + x86_64.
    option(PSXL_UNIVERSAL "Build a universal (arm64 + x86_64) binary" OFF)
    if(PSXL_UNIVERSAL)
        set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "" FORCE)
    else()
        set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "" FORCE)
    endif()
    set(CMAKE_OSX_DEPLOYMENT_TARGET "11.0" CACHE STRING "" FORCE)
endif()

project(MassivePSXL VERSION 1.0.0 LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
set(FETCHCONTENT_QUIET OFF)
FetchContent_Declare(JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 8.0.8
    GIT_SHALLOW ON)
FetchContent_MakeAvailable(JUCE)

# ---- embedded resources: factory presets + artwork (artwork files are optional) ----
set(PSXL_RESOURCES Resources/presets/factory_presets.xml)
foreach(art bg_dark.png bg_light.png logo_wordmark.png logo_mark.png waveform_bar.png splash.png)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/Resources/art/${art}")
        list(APPEND PSXL_RESOURCES "Resources/art/${art}")
    endif()
endforeach()
juce_add_binary_data(PSXLData SOURCES ${PSXL_RESOURCES})
set_target_properties(PSXLData PROPERTIES POSITION_INDEPENDENT_CODE ON)

set(PSXL_ICON "${CMAKE_CURRENT_SOURCE_DIR}/Resources/art/icon_1024.png")
set(PSXL_ICON_SMALL "${CMAKE_CURRENT_SOURCE_DIR}/Resources/art/icon_256.png")
set(PSXL_ICON_ARGS "")
if(EXISTS "${PSXL_ICON}")
    set(PSXL_ICON_ARGS ICON_BIG "${PSXL_ICON}" ICON_SMALL "${PSXL_ICON_SMALL}")
endif()

juce_add_plugin(MassivePSXL
    COMPANY_NAME "Phil S Audio"
    COMPANY_WEBSITE "https://philsaudio.example"
    BUNDLE_ID com.philsaudio.massivepsxl
    PRODUCT_NAME "Massive PSXL"
    PLUGIN_NAME "Massive PSXL"
    PLUGIN_MANUFACTURER_CODE PhSA
    PLUGIN_CODE Psxl
    FORMATS VST3 AU Standalone
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS TRUE
    COPY_PLUGIN_AFTER_BUILD FALSE
    VST3_CATEGORIES Instrument Synth
    AU_MAIN_TYPE kAudioUnitType_MusicDevice
    ${PSXL_ICON_ARGS})

target_sources(MassivePSXL PRIVATE
    Source/Params.cpp
    Source/PluginProcessor.cpp
    Source/PresetManager.cpp
    Source/dsp/Wavetable.cpp
    Source/dsp/Engine.cpp
    Source/ui/Widgets.cpp
    Source/ui/RoutingView.cpp
    Source/ui/ModViews.cpp
    Source/ui/OtherViews.cpp
    Source/ui/Panels.cpp
    Source/ui/PluginEditor.cpp)

target_include_directories(MassivePSXL PUBLIC Source)
target_compile_definitions(MassivePSXL PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0)

target_link_libraries(MassivePSXL
    PRIVATE
        PSXLData
    PUBLIC
        juce::juce_audio_utils
        juce::juce_audio_processors
        juce::juce_audio_formats
        juce::juce_dsp
        juce::juce_gui_extra
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags)

# ---- offline engine test (renders audio without a host) ----
option(PSXL_BUILD_TESTS "Build the offline engine test" ON)
if(PSXL_BUILD_TESTS)
    juce_add_console_app(PSXLTest PRODUCT_NAME "psxl_test")
    target_sources(PSXLTest PRIVATE tests/engine_test.cpp)
    target_link_libraries(PSXLTest PRIVATE MassivePSXL juce::juce_recommended_config_flags)
    target_compile_definitions(PSXLTest PRIVATE JUCE_USE_CURL=0 JUCE_WEB_BROWSER=0)
endif()

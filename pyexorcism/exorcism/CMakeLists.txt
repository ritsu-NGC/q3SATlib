cmake_minimum_required (VERSION 3.6)

project(exorcism LANGUAGES CXX)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

include_directories(${PROJECT_SOURCE_DIR})

file(GLOB ABC_SRC *.cpp)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)


# Surpress warnings in external library
if (UNIX)
    add_compile_options("-w")
elseif (MSVC)
    string(REPLACE "/W3" "/w" CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS})
endif()

if (STATIC_LIBABC)
    add_library(exorcism STATIC EXCLUDE_FROM_ALL ${ABC_SRC})
    set_property(TARGET exorcism PROPERTY OUTPUT_NAME exorcism)
else()
    add_library(exorcism SHARED EXCLUDE_FROM_ALL ${ABC_SRC})
    set_property(TARGET exorcism PROPERTY OUTPUT_NAME exorcism)
    set_property(TARGET exorcism PROPERTY POSITION_INDEPENDENT_CODE ON)
endif()

target_include_directories(exorcism PRIVATE ${Python3_INCLUDE_DIRS})

target_include_directories(exorcism
    PRIVATE ${Python3_INCLUDE_DIRS}
    INTERFACE
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}>
        $<INSTALL_INTERFACE:include>
)
install(DIRECTORY ${PROJECT_SOURCE_DIR}/
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
        FILES_MATCHING PATTERN "*.h" PATTERN "*.hpp")
install(TARGETS exorcism EXPORT exorcismTargets)
install(EXPORT exorcismTargets NAMESPACE exorcism:: DESTINATION lib/cmake/exorcism)

if (UNIX)
    target_compile_definitions(exorcism PUBLIC "LIN64" ABC_NO_USE_READLINE)
elseif(WIN32)
    target_compile_definitions(exorcism PUBLIC ABC_USE_NO_READLINE NOMINMAX  WIN32_NO_DLL _CRT_SECURE_NO_WARNINGS)
endif()



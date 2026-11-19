set(cluster_sources
    "app.cpp"
    "board.cpp"
    "../core/controls.cpp"
    "../core/history.cpp"
    "../ui/dashboard.cpp"
    "../assets/cluster_icons.c"
    "../assets/cluster_num_64.c"
    "../assets/cluster_num_96.c"
    "../assets/cluster_num_144.c"
    "../assets/cluster_num_220.c"
    "../assets/cluster_text_26.c"
    "../assets/cluster_text_34.c")

if(CONFIG_CLUSTER_LIVE)
    list(APPEND cluster_sources "uart.cpp" "../core/protocol.cpp")
else()
    list(APPEND cluster_sources "../core/replay.cpp")
endif()
if(CONFIG_CLUSTER_ADS1115)
    list(APPEND cluster_sources "ads1115.cpp" "../core/calibration.cpp")
endif()
if(CONFIG_CLUSTER_SD_LOGGING)
    list(APPEND cluster_sources "sd_logger.cpp")
endif()

idf_component_register(SRCS ${cluster_sources}
                       PRIV_INCLUDE_DIRS "../include"
                       PRIV_REQUIRES esp_driver_gpio esp_driver_uart esp_driver_i2c
                                     esp_timer esp_psram nvs_flash fatfs esp_driver_sdmmc sdmmc)
target_compile_features(${COMPONENT_LIB} PRIVATE cxx_std_17)
target_compile_definitions(${COMPONENT_LIB} PRIVATE LV_LVGL_H_INCLUDE_SIMPLE)

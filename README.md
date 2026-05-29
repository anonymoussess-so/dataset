#自然灾害通信资源数据集说明

该数据集面向自然灾害应急通信资源调度任务构建，基于链路测量、业务会话测量和核心网话单等多源通信数据，经字段清洗、时间对齐、节点关联和业务聚合后形成，用于描述灾害场景下通信资源能力、节点状态和用户业务需求

## 总体目录结构

```text
data/extreme_disaster_resources/
|- README.md
|- metadata.json
|- regions.json
|- extreme_rainstorm/
|- super_typhoon/
`- destructive_earthquake/
   `- <disaster_severity>/
      |- severity_description.md
      `- <communication_type>/
         `- <base_station_type>/
         |- resource_profile.json
         |- cell_info.jsonl
         `- business_users.jsonl
```

整体层级为：

```text
自然灾害场景(region/disaster_scenario)
  -> 受灾程度(disaster_severity)
    -> 通信类型(communication_type)
      -> 基站/资源类型(base_station_type)
        -> 基站画像 + 部署样本 + 用户业务会话
```


## 场景网格与受灾面积

| 灾害场景 | 网格行列 | 网格总数 | 受灾面积(km²) | 单网格面积(km²) |
|---|---:|---:|---:|---:|
| 地震场景 | 5×12 | 60 | 480 | 8.000 |
| 台风场景 | 20×12 | 240 | 2040 | 8.500 |
| 暴雨场景 | 10×12 | 120 | 900 | 7.500 |

三类灾害场景采用不同网格尺寸，是为了反映不同灾害的空间影响范围：地震场景范围较集中，使用 5×12 网格描述约 480 km² 的重点受灾区；台风场景影响范围更大，使用 20×12 网格描述约 2040 km² 的沿海受灾带；暴雨场景使用 10×12 网格描述约 900 km² 的南阳局地强降雨影响区。`cell_info.jsonl.grid_position.row/col` 的取值范围由对应场景的 `region_grid.rows/cols` 决定。

## 数据规模

当前默认整理结果：

| 指标 | 数量 |
|---|---:|
| 灾害场景 | 3 |
| 通信类型 | 4 |
| 受灾程度 | 4 |
| 单个受灾程度下基站/资源类型 | 10 |
| 场景化基站画像 | 120 |
| 部署样本 | 1260 |
| 用户业务会话 | 2880000 |

## 顶层目录和文件

### `README.md`

当前说明文档，描述数据集目录结构、文件用途和字段含义。

### `metadata.json`

数据集元信息文件，记录层级结构、灾害场景数量、通信类型数量、样本总量和全局业务统计。

### `regions.json`

自然灾害场景汇总文件。它把每个灾害场景、受灾程度下的通信模式、基站类型、覆盖范围、最大带宽、连接成功率、失败率、平均时延、部署样本数量和 72 个时间步的资源变化整理成一个紧凑结构，适合后续训练环境或评估程序读取。

### `extreme_rainstorm/`

超强暴雨场景。表示城市内涝、供电不稳、低洼区域用户向避险点聚集，蜂窝网络仍有残余能力，卫星链路受雨衰影响，WiFi 热点受进水和断电影响。

### `super_typhoon/`

特大台风场景。表示强风、风暴潮和长时间停电造成沿海宏站倒伏、回传中断，蜂窝覆盖和带宽下降，卫星和短波承担跨区域回传与应急通信。

### `destructive_earthquake/`

强破坏地震场景。表示基站、传输光缆和供电设施发生物理损毁，残余公网能力较弱，主要依靠应急车、小站、卫星、短波和临时 WiFi Mesh 恢复通信。

## 灾害场景目录结构

每个灾害场景目录下都有 4 个受灾程度目录，每个受灾程度目录下都有 4 类通信类型目录：

```text
<disaster_scenario>/
|- level_1/
|- level_2/
|- level_3/
`- level_4/
   |- cellular_5g_700mhz/
   |- satellite_ka/
   |- wifi6_mesh/
   `- shortwave_hf/
```

受灾程度目录含义：

| 目录名 | 中文含义 | 通信资源变化 |
|---|---|---|
| `level_1` | 受灾等级一 | 少量基站受损，带宽轻微下降，连接成功率较高，恢复快。 |
| `level_2` | 受灾等级二 | 部分基站或回传受损，带宽明显下降，时延和失败率上升。 |
| `level_3` | 受灾等级三| 大面积断电、断站或拥塞，蜂窝可用率低，卫星和短波占比上升。 |
| `level_4` | 受灾等级四 | 残余公网极弱或不可用，主要依赖卫星、短波、应急车、临时 WiFi Mesh。 |


受灾等级划分原因：

| 划分目的 | 说明 |
|---|---|
| 区分灾害强度 | 同一灾害类型下，不同强度会造成不同范围的站点损毁、供电中断、回传中断和用户聚集。使用 `level_1` 到 `level_4` 可以把灾害影响从轻到重分层表达。 |
| 支撑强化学习状态输入 | 强化学习模型需要明确当前处于哪一级灾情，才能学习不同等级下的资源退化规律和调度策略。 |
| 支撑动作约束 | 受灾等级越高，离线站点比例、带宽下降、覆盖收缩和业务失败率通常越高，可选动作和可用资源也会发生变化。 |
| 支撑奖励计算 | 不同等级下，覆盖恢复、连接成功率、业务吞吐、时延和资源消耗的权重不同，等级划分可以使奖励函数具备阶段差异。 |
| 支撑实验评估 | 将灾情划分为四级后，可以分别评估模型在轻灾、中灾、重灾和极端灾情下的鲁棒性和泛化能力。 |

等级判断不是由单个字段直接决定，而是综合 `cell_info.jsonl` 和 `business_users.jsonl` 中的站点状态、受损比例、离线比例、连接成功率、带宽、覆盖范围、时延、重传和乱序等指标得到。目录名只保留 `level_1` 到 `level_4`，中文标签分别对应一般、中等、严重和特别严重，避免在目录层级中混用英文描述。

| 目录名 | `communication_type` | 含义 |
|---|---|---|
| `cellular_5g_700mhz` | `5G_700MHz` | 5G 700 MHz 蜂窝通信资源 |
| `satellite_ka` | `Satellite_Ka` | Ka 频段卫星通信资源 |
| `wifi6_mesh` | `WiFi6` | WiFi 6 Mesh 应急接入资源 |
| `shortwave_hf` | `Shortwave_HF` | 短波 HF 兜底通信资源 |

## 通信类型目录结构

```text
cellular_5g_700mhz/
|- low_band_macro_cell/
|- temporary_macro_cell/
`- backpack_micro_cell/

satellite_ka/
|- vehicle_satellite_terminal/
`- fixed_satellite_gateway/

wifi6_mesh/
|- portable_hotspot/
|- vehicle_wifi_node/
`- shelter_mesh_node/

shortwave_hf/
|- field_shortwave_station/
`- command_vehicle_radio/
```

每个基站/资源目录下都有 3 个文件：

```text
<base_station_type>/
|- resource_profile.json
|- cell_info.jsonl
`- business_users.jsonl
```

## `severity_description.md`

该文件位于每个受灾程度目录下，例如 `destructive_earthquake/level_3/severity_description.md`。它用于解释该受灾等级的判断方法、对应灾害强度、典型破坏形态，以及该等级下通信资源可能出现的带宽下降、覆盖收缩、站点离线和业务质量退化情况。该文件描述的是场景级受灾程度，而不是单个基站的运行状态。

## `resource_profile.json`

该文件描述某个灾害场景、某种通信类型、某类基站资源的总体画像。它可以理解为该基站类型下面所有部署样本和用户业务的汇总。

| 字段 | 类型 | 说明 |
|---|---|---|
| `resource_id` | string | 资源画像唯一标识，格式通常为 `<disaster_scenario>_<disaster_severity>_<communication_directory>_<base_station_type>`。 |
| `region` | string | 顶层场景名。这里的 region 等同于自然灾害场景，例如 `extreme_rainstorm`。 |
| `region_label` | string | 灾害场景中文名，例如 `超强暴雨`。 |
| `disaster_scenario` | string | 灾害场景英文标识，与 `region` 相同。 |
| `disaster_label` | string | 灾害场景中文标签。 |
| `disaster_type` | string | 灾害类别，例如 `rainstorm`、`typhoon`、`earthquake`。 |
| `disaster_severity` | string | 受灾程度目录名，例如 `level_3`。 |
| `disaster_severity_label` | string | 受灾程度中文标签。 |
| `disaster_severity_description` | string | 受灾程度对通信资源的影响描述。 |
| `has_residual_network` | boolean | 是否存在残余公网能力。 |
| `scenario_characteristics` | array[string] | 灾害场景特征描述。 |
| `communication_type` | string | 通信类型，如 `5G_700MHz`、`Satellite_Ka`。 |
| `communication_directory` | string | 通信类型对应的目录名，如 `cellular_5g_700mhz`。 |
| `communication_label` | string | 通信类型可读名称。 |
| `base_station_type` | string | 基站/资源类型目录名，如 `macro_cell`。 |
| `base_station_label` | string | 基站/资源类型可读名称。 |
| `base_station_role` | string | 该基站/资源在应急通信中的作用说明。 |
| `deployment_sample_count` | integer | 该资源类型下的真实站点/节点数量。 |
| `measurement_periods` | array[object] | 该资源画像包含的时间批次，分为历史数据和新采集数据。 |
| `cell_user_count` | integer | 该基站/资源类型对应的 cell 用户数估计值。 |
| `downlink_bandwidth_mbps` | object | 下行带宽统计，单位 Mbps。包含 `min`、`max`、`avg`。 |
| `uplink_bandwidth_mbps` | object | 上行带宽统计，单位 Mbps。包含 `min`、`max`、`avg`。 |
| `mss_bytes` | integer | MSS，单位 byte。 |
| `connection_attempt_count` | integer | 该资源类型下所有业务会话的连接尝试次数汇总。 |
| `connection_success_count` | integer | 该资源类型下连接成功的业务会话数量。 |
| `connection_failure_count` | integer | 该资源类型下连接失败的业务会话数量。 |
| `connection_success_rate` | number | 连接成功率，取值 0 到 1，由该资源类型下所有 `business_users.jsonl` 会话按 `connection_success_count / connection_attempt_count` 统计得到。 |
| `connection_failure_rate` | number | 连接失败率，等于 `connection_failure_count / connection_attempt_count`，也等于 `1 - connection_success_rate`。 |
| `average_business_throughput_mbps` | number | 根据业务会话中的视频吞吐统计得到的平均业务吞吐，单位 Mbps。 |
| `coverage_radius_km` | number | 覆盖半径，单位 km。 |
| `tx_power_watt` | number | 发射功率，单位 W。 |
| `deployment_summary` | object | 该资源类型下真实站点的数量、损毁状态、唯一网格和有效覆盖面积汇总。 |
| `operation_status_summary` | object | 根据 `cell_info.jsonl` 真实站点统计得到的运行状态汇总。 |

常见子结构：

| 子结构 | 字段 | 说明 |
|---|---|---|
| `downlink_bandwidth_mbps` / `uplink_bandwidth_mbps` | `min`、`max`、`avg` | 最小、最大和平均带宽。 |
| `deployment_summary` | `physical_station_count`、`active_station_count`、`degraded_station_count`、`offline_station_count`、`damaged_station_count`、`unique_grid_count`、`effective_covered_grid_count`、`estimated_grid_area_km2`、`estimated_effective_grid_area_km2` | 真实站点数量、损毁数量、唯一网格数量和有效覆盖面积。 |
| `operation_status_summary` | `status_counts`、`status_ratio`、`damaged_station_ratio`、`offline_station_ratio`、`dominant_status` | 由该资源类型下所有真实站点的 `operational_status` 和损毁字段统计得到，表示当前资源类型的整体运行状态分布。 |

## 通信制式和基站类型指标参考

本节统计口径为当前数据集中三种灾害场景和四种受灾程度的整体范围。带宽与覆盖半径已经叠加灾害场景、受灾程度、站点类型和损毁状态影响，因此同一通信制式在不同灾情下会出现不同取值。

### 通信制式定义和总体范围

| 通信制式 | 定义 | 特点 | 典型下行带宽范围(Mbps) | 典型上行带宽范围(Mbps) | 覆盖半径范围(km) | 站点/节点数 | 有效网格数 | 用户数合计 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `5G_700MHz` | 700 MHz 低频 5G 蜂窝公网/应急小区接入。 | 覆盖较远、穿透较好，适合公众接入和应急车小区；灾害中易受断电、倒站、回传中断影响。 | 2.265-98.097 | 0.952-41.201 | 0.152-2.349 | 360 | 281 | 70570 |
| `Satellite_Ka` | Ka 频段卫星接入和回传链路。 | 对地面基础设施依赖少、覆盖广；带宽较高但受雨衰、遮挡和终端数量影响，适合指挥点、医院、避难所回传。 | 10.137-52.806 | 2.838-14.786 | 3.569-9.193 | 120 | 107 | 19400 |
| `WiFi6` | WiFi 6 临时热点和 Mesh 接入。 | 短距离、高容量、部署快；依赖本地供电和回传，适合避难所、救援点和应急车辆周边。 | 3.957-38.937 | 2.176-21.416 | 0.058-0.300 | 672 | 553 | 45439 |
| `Shortwave_HF` | 短波 HF 远距离保底通信。 | 速率低但距离远，对公网和传输基础设施依赖低，适合语音、低速数据、指挥调度和告警兜底。 | 0.088-0.419 | 0.058-0.272 | 10.062-24.200 | 108 | 97 | 2791 |

### 基站/节点类型指标

| 通信制式 | 基站/节点类型 | 定义与用途 | 典型下行带宽范围(Mbps) | 典型上行带宽范围(Mbps) | 覆盖半径范围(km) | 站点/节点数 | 有效网格数 | 用户数合计 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `5G_700MHz` | `low_band_macro_cell` | 低频宏站，提供较大范围公网覆盖和较强穿透能力。 | 7.839-98.097 | 3.292-41.201 | 0.569-2.349 | 120 | 91 | 33689 |
| `5G_700MHz` | `temporary_macro_cell` | 临时宏站/应急车小区，用于区域覆盖恢复和容量补充。 | 5.692-81.903 | 2.391-34.399 | 0.386-1.594 | 96 | 79 | 23945 |
| `5G_700MHz` | `backpack_micro_cell` | 背包式微站，服务救援队和孤立小范围用户簇。 | 2.265-32.817 | 0.952-13.783 | 0.152-0.629 | 144 | 111 | 12936 |
| `Satellite_Ka` | `vehicle_satellite_terminal` | 车载 Ka 卫星终端，用于移动指挥车、应急车和临时回传。 | 10.137-31.591 | 2.838-8.845 | 3.569-6.402 | 72 | 67 | 10558 |
| `Satellite_Ka` | `fixed_satellite_gateway` | 固定式 Ka 卫星网关，用于避难所、医院和指挥中心的高容量回传。 | 15.638-52.806 | 4.379-14.786 | 5.125-9.193 | 48 | 40 | 8842 |
| `WiFi6` | `portable_hotspot` | 便携 WiFi 6 热点，服务小型救援点和临时安置点。 | 3.957-17.362 | 2.176-9.549 | 0.058-0.146 | 240 | 196 | 11622 |
| `WiFi6` | `vehicle_wifi_node` | 车载 WiFi 6 节点，服务应急车辆周边和移动服务点。 | 5.628-24.692 | 3.095-13.580 | 0.119-0.300 | 144 | 117 | 9403 |
| `WiFi6` | `shelter_mesh_node` | 避难所 Mesh 节点，服务密集安置区、本地缓存和短距离接入。 | 7.896-38.937 | 4.343-21.416 | 0.085-0.214 | 288 | 240 | 24414 |
| `Shortwave_HF` | `field_shortwave_station` | 野外短波台站，提供低速远距离指挥和遥测链路。 | 0.088-0.259 | 0.058-0.168 | 10.062-17.456 | 60 | 55 | 1471 |
| `Shortwave_HF` | `command_vehicle_radio` | 指挥车短波电台，提供更强发射能力和更大范围的现场指挥通信。 | 0.138-0.419 | 0.090-0.272 | 13.950-24.200 | 48 | 42 | 1320 |

## `cell_info.jsonl`

该文件是 JSON Lines 格式，每一行是一个真实基站/节点。它表示在该灾害场景、通信类型和基站类型下，某个具体 cell/节点的部署位置、损毁状态、覆盖、用户数和带宽统计。

| 字段 | 类型 | 说明 |
|---|---|---|
| `deployment_id` | string | 部署样本唯一标识。 |
| `measurement_period` | string | 时间批次，取值为 `historical` 或 `new_collection`。 |
| `collection_date` | string | 采集日期。历史数据为 2023 年日期，新采集数据按灾害场景固定到指定日期。 |
| `region` | string | 顶层灾害场景名，与 `disaster_scenario` 相同。 |
| `region_label` | string | 灾害场景中文名。 |
| `disaster_scenario` | string | 灾害场景英文标识。 |
| `disaster_label` | string | 灾害场景中文标签。 |
| `disaster_type` | string | 灾害类别。 |
| `disaster_severity` | string | 受灾程度目录名。 |
| `disaster_severity_label` | string | 受灾程度中文标签。 |
| `communication_type` | string | 通信类型。 |
| `communication_directory` | string | 通信类型目录名。 |
| `base_station_type` | string | 基站/资源类型。 |
| `base_station_label` | string | 基站/资源中文或英文可读名称。 |
| `grid_position` | object | 网格坐标，包含 `row` 和 `col`。取值范围按场景变化：地震 row=0-4、col=0-11；台风 row=0-19、col=0-11；暴雨 row=0-9、col=0-11。 |
| `geo_position` | object | 经纬度位置，包含 `lat` 和 `lon`。地震和台风场景从预设候选坐标中取值，暴雨场景固定为指定坐标。 |
| `work_time_periods` | array[object] | 工作时间段。 |
| `is_damaged` | boolean | 该站点/节点是否受灾损毁或受损。 |
| `damage_level` | string | 损毁程度，取值包括 `intact`、`minor_damage`、`major_damage`、`offline`。 |
| `damage_ratio` | number | 损毁比例估计值，范围 0 到 1。 |
| `operational_status` | string | 当前运行状态，取值包括 `active`、`degraded`、`offline`。该字段不是预先指定，而是由 `status_judgement` 中的阈值规则根据站点实测指标判定。 |
| `status_judgement` | object | 基站状态判定过程，包含判定方法、规则版本、带宽保持率、覆盖保持率、用户承载保持率、连接成功率、损毁比例和触发规则。 |
| `distance_to_disaster_core_grid` | number | 该站点到灾害核心区域的网格距离。 |
| `is_in_damage_core` | boolean | 是否处于灾害核心损毁区域。 |
| `cell_user_count` | integer | 该部署样本对应的 cell 用户数。 |
| `downlink_bandwidth_mbps` | object | 下行带宽统计，包含 `min`、`max`、`avg`。 |
| `uplink_bandwidth_mbps` | object | 上行带宽统计，包含 `min`、`max`、`avg`。 |
| `mss_bytes` | integer | MSS，单位 byte。 |
| `connection_attempt_count` | integer | 该基站关联业务会话的连接尝试次数。 |
| `connection_success_count` | integer | 该基站关联业务会话中连接成功的次数。 |
| `connection_failure_count` | integer | 该基站关联业务会话中连接失败的次数。 |
| `connection_statistics` | object | 连接成功率的统计口径，包含聚合单位、尝试次数、成功次数和失败次数。 |
| `connection_success_rate` | number | 连接成功率，由同一 `deployment_id` 下业务会话的 `connection_success` 聚合统计得到。 |
| `connection_failure_rate` | number | 连接失败率，由同一 `deployment_id` 下业务会话的 `connection_failure` 聚合统计得到。 |
| `coverage_radius_km` | number | 覆盖半径，单位 km。 |
| `tx_power_watt` | number | 发射功率，单位 W。 |

### 基站状态判定逻辑

`cell_info.jsonl` 中的 `operational_status` 可以理解为现场网管指标、巡检指标和业务会话统计汇总后的判定结果。生成逻辑先得到每个站点的下行平均带宽、覆盖半径、承载用户数和损毁比例，再把同一 `deployment_id` 下的业务会话按连接成功/失败次数统计成 `connection_success_rate`，最后和该站点类型在当前灾情下的基准能力比较，形成以下归一化指标：

| 判定指标 | 含义 |
|---|---|
| `bandwidth_ratio` | 当前下行平均带宽 / 当前资源画像中的基准下行平均带宽。 |
| `coverage_ratio` | 当前覆盖半径 / 当前资源画像中的基准覆盖半径。 |
| `user_ratio` | 当前承载用户数 / 当前资源画像中的基准用户数。 |
| `connection_success_rate` | 当前站点连接成功率。 |
| `damage_ratio` | 结合站点位置、灾害核心距离和受灾程度得到的损毁比例估计。 |

连接成功率的统计公式为：

```text
connection_success_rate = connection_success_count / connection_attempt_count
connection_failure_rate = connection_failure_count / connection_attempt_count
connection_failure_count = connection_attempt_count - connection_success_count
```

其中 `connection_attempt_count`、`connection_success_count` 和 `connection_failure_count` 来自同目录 `business_users.jsonl` 中与该基站 `deployment_id` 相同的业务会话记录。

状态判定规则如下：

| 状态 | 判定条件 |
|---|---|
| `offline` | 覆盖半径接近 0、承载用户数为 0、连接成功率小于 0.08、带宽保持率小于 0.05，或损毁比例不小于 0.85。满足任一条件即判为离线。 |
| `degraded` | 未达到离线条件，但损毁比例不小于 0.15、带宽保持率小于 0.70、覆盖保持率小于 0.80、连接成功率小于 0.60，或用户承载保持率小于 0.70。满足任一条件即判为降级。 |
| `active` | 未触发离线或降级条件，说明主要运行指标仍在可用阈值内。 |

`operational_status` 表示站点当前能不能正常服务，主要由运行指标决定；`damage_level` 表示物理损毁或受灾损伤程度，主要由 `damage_ratio` 决定。两者不必完全相同：例如某个站点本体未损毁，但因为回传拥塞或链路质量下降，可能出现 `damage_level=intact` 且 `operational_status=degraded`；离线站点记为 `damage_level=offline`。

## `business_users.jsonl`

该文件是 JSON Lines 格式，每一行是一条用户/业务会话。它位于具体基站类型目录下，因此可以理解为该类基站服务到的用户业务样本。

| 字段 | 类型 | 说明 |
|---|---|---|
| `session_id` | string | 用户业务会话唯一标识。 |
| `user_id` | string | 用户标识。 |
| `deployment_id` | string | 该业务会话关联的部署样本 ID。 |
| `measurement_period` | string | 时间批次，取值为 `historical` 或 `new_collection`。 |
| `collection_date` | string | 采集日期。历史数据为 2023 年日期，新采集数据按灾害场景固定到指定日期。 |
| `region` | string | 顶层灾害场景名，与 `disaster_scenario` 相同。 |
| `region_label` | string | 灾害场景中文名。 |
| `disaster_scenario` | string | 灾害场景英文标识。 |
| `disaster_label` | string | 灾害场景中文标签。 |
| `disaster_type` | string | 灾害类别。 |
| `disaster_severity` | string | 受灾程度目录名。 |
| `disaster_severity_label` | string | 受灾程度中文标签。 |
| `communication_type` | string | 通信类型。 |
| `base_station_type` | string | 基站/资源类型。 |
| `service_type` | string | 业务类型或业务名称，例如视频 App 名称或 XDR 业务类型。 |
| `service_code` | string | 业务编码。 |
| `duration_ms` | number | 业务持续时间，单位 ms。 |
| `data_volume_bytes` | integer | 业务总数据量，单位 byte，通常为上下行数据量之和。 |
| `downlink_bytes` | integer | 下行数据量，单位 byte。 |
| `uplink_bytes` | integer | 上行数据量，单位 byte。 |
| `reordering_packet_count` | integer | TCP 乱序报文总数，上下行合并。 |
| `retransmission_packet_count` | integer | TCP 重传报文总数，上下行合并。 |
| `latency_ms` | number | 业务时延，单位 ms。 |
| `start_time` | string | 业务开始时间，ISO 时间格式。 |
| `end_time` | string | 业务结束时间，ISO 时间格式。 |
| `mss_bytes` | integer | MSS，单位 byte。 |
| `play_success` | integer | 播放成功标志，通常 `1` 表示成功，`0` 表示失败。 |
| `connection_attempt_count` | integer | 该业务会话对应的连接尝试次数，当前每条会话为 1 次尝试。 |
| `connection_success` | integer | 该业务会话连接是否成功，`1` 表示成功，`0` 表示失败。 |
| `connection_failure` | integer | 该业务会话连接是否失败，`1` 表示失败，`0` 表示成功。 |
| `startup_delay_ms` | number | 视频起播等待时间，单位 ms。 |
| `stall_count` | integer | 视频卡顿次数。 |
| `stall_duration_ms` | number | 视频卡顿总时长，单位 ms。 |
| `video_throughput_kbps` | number | 视频下载吞吐，单位 Kbps。 |
| `video_bitrate_kbps` | number | 视频码率，单位 Kbps。 |
| `first_segment_size_bytes` | integer | 首段视频大小，单位 byte。 |
| `bandwidth_trace_mbps` | array[number] | 传输过程中的带宽变化序列，单位 Mbps。 |
| `rat_type` | any | 无线接入类型；部分业务会话可能不存在。 |
| `bearer_qci` | any | Bearer QCI；部分业务会话可能不存在。 |
| `ecgi` | any | 小区 ECGI；部分业务会话可能不存在。 |

## `metadata.json`

| 字段 | 类型 | 说明 |
|---|---|---|
| `dataset_name` | string | 数据集名称。 |
| `dataset_type` | string | 数据集类型，当前为实测融合整理数据。 |
| `schema_hierarchy` | string | 数据集层级结构说明。 |
| `disaster_scenario_count` | integer | 灾害场景数量。 |
| `disaster_severity_count` | integer | 受灾程度数量。 |
| `disaster_severity_levels` | object | 受灾程度配置及其对通信资源指标的影响。 |
| `disaster_scenarios` | object | 灾害场景元信息，key 为场景名。 |
| `communication_type_count` | integer | 通信类型数量。 |
| `unique_base_station_type_count` | integer | 单个场景下的基站/资源类型数量。 |
| `scenario_base_station_profile_count` | integer | 场景化基站画像总数。 |
| `deployment_sample_count` | integer | 部署样本总数。 |
| `business_session_count` | integer | 用户业务会话总数。 |
| `measurement_periods` | object | 历史数据和新采集数据的时间范围说明。 |
| `global_business_summary` | object | 全局业务统计，包括持续时间、数据量、时延、吞吐、播放成功率、MSS、TCP 乱序和重传均值。 |

## `regions.json`

该文件的顶层字段为 `scenarios`，其中每个元素对应一个自然灾害场景。

每个场景对象包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | 灾害场景英文标识。 |
| `label` | string | 灾害场景中文名。 |
| `disaster_type` | string | 灾害类别。 |
| `disaster_characteristics` | array[string] | 灾害场景特征描述。 |
| `has_residual_network` | boolean | 是否存在残余公网能力。 |
| `grid_rows` / `grid_cols` | integer | 场景网格行数和列数。当前地震为 5×12，台风为 20×12，暴雨为 10×12。 |
| `region_grid` | object | 场景网格定义，包含 `rows`、`cols`、`grid_count`、`geo_bounds`、`affected_area_km2`、`coverage_area_km2` 和 `grid_cell_area_km2`。暴雨场景经纬度为单点，但使用面积字段表示南阳局地强降雨覆盖范围。 |
| `communication_modes` | array[string] | 该场景包含的通信类型。 |
| `severity_levels` | object | 每个受灾程度下的通信制式画像和 72 个时间步资源变化。 |

`mode_metrics` 中每个通信类型对象包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `available_bandwidth` | number | 该时间步可用带宽，单位 Mbps。 |
| `availability` | number | 该时间步可用率/连接成功率估计值。 |

`severity_levels.<level>.mode_profiles` 中每个通信类型对象包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `coverage_radius` | number | 该受灾程度和通信类型下的平均覆盖半径，单位 km。 |
| `max_bandwidth` | number | 该受灾程度和通信类型下的最大下行带宽，单位 Mbps。 |
| `average_success_rate` | number | 该受灾程度和通信类型下的平均连接成功率。 |
| `average_failure_rate` | number | 该受灾程度和通信类型下的平均连接失败率。 |
| `deployment_sample_count` | integer | 该受灾程度和通信类型下的部署样本数量。 |
| `physical_station_count` | integer | 该受灾程度和通信类型下的真实站点/节点数量。 |
| `damaged_station_count` | integer | 该受灾程度和通信类型下的受损站点/节点数量。 |
| `offline_station_count` | integer | 该受灾程度和通信类型下的离线站点/节点数量。 |
| `base_station_types` | array[string] | 该通信类型包含的基站/资源类型目录名。 |

`severity_levels.<level>.time_series` 中每个时间步对象包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `time` | integer | 时间步序号，范围为 0 到 71。 |
| `mode_metrics` | object | 当前时间步下各通信类型的可用带宽和可用率。 |

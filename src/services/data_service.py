"""
src/services/data_service.py
"""
import time
import sqlite3
import csv
import os
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from threading import Lock
from pathlib import Path
from config.config_system import config_manager
from PySide6.QtCore import QObject


# --- 基础类定义 (避免循环导入) ---
class BaseService(QObject):
    def __init__(self, name): super().__init__()


class ServiceStatus:
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class ServiceError(Exception):
    pass


# --- DataService 主类 ---
class DataService(BaseService):
    def __init__(self, db_path: str = "data/system.db", csv_dir: str = "data/csv",
                 tag_list_file: str = "resources/tags/tagList.csv"):
        super().__init__("data_service")
        self.db_path = db_path
        self.csv_dir = Path(csv_dir)
        self.tag_list_file = tag_list_file

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()

        # 1. 药剂列映射 [数据库列名 -> OPC标签名]
        self.reagent_mapping = {
            'qkc_dinghuangyao1': 'YJ.yj_qkc_dinghuangyao1:actualflow',
            'qkc_dinghuangyao2': 'YJ.yj_qkc_dinghuangyao2:actualflow',
            'qkc_yiliudan1': 'YJ.yj_qkc_yiliudan1:actualflow',
            'qkc_yiliudan2': 'YJ.yj_qkc_yiliudan2:actualflow',
            'qkc_shihui': 'YJ.yj_qkc_shihui:actualflow',
            'qkc_5_you': 'YJ.yj_qkc_5#you:actualflow',
            'qkj1_dinghuangyao': 'YJ.yj_qkj1_dinghuangyao:actualflow',
            'qkj1_yiliudan': 'YJ.yj_qkj1_yiliudan:actualflow',
            'qkj1_shihui': 'YJ.yj_qkj1_shihui:actualflow',
            'qkj2_yiliudan': 'YJ.yj_qkj2_yiliudan:actualflow',
            'qkj2_shihui': 'YJ.yj_qkj2_shihui:actualflow',
            'qkj2_dinghuangyao': 'YJ.yj_qkj2_dinghuangyao:actualflow',
            'qkj3_dinghuangyao': 'YJ.yj_qkj3_dinghuangyao:actualflow',
            'qkj3_yiliudan': 'YJ.yj_qkj3_yiliudan:actualflow',
            'qkj3_ds1': 'YJ.yj_qkj3_ds1:actualflow',
            'qkj3_ds2': 'YJ.yj_qkj3_ds2:actualflow',
            'qkj3_shihui': 'YJ.yj_qkj3_shihui:actualflow'
        }
        # 2. [新增] 品位/工况映射 [数据库列名(逻辑名) -> OPC标签名]
        # 提取自 _save_to_sqlite 中的硬编码
        self.grade_mapping = {
            'feed_grade_Pb': 'KYFX.kyfx_yk_grade_Pb',  # 原矿品位
            'conc_grade_Pb': 'KYFX.kyfx_gqxk_grade_Pb',  # 精矿品位
            'tail_grade_Pb': 'KYFX.kyfx_qw_grade_Pb',  # 尾矿品位 (用于计算回收率)
            'conc_total_Pb': 'KYFX.kyfx_zqxk_grade_Pb'  # 综合精矿 (用于计算回收率)
        }

        # 3. 泡沫特征映射 [数据库列名 -> AnalysisService字典Key]
        # 扩展了颜色(RGB/HSV/统计)、纹理(GLCM)、形态(分布/圆度)及动态(方差)特征
        self.froth_mapping = {
            # --- 核心指标 (原有) ---
            'froth_mean_diam': 'bubble_mean_diam',  # 平均粒径
            'froth_bubble_count': 'bubble_count',  # 气泡数量
            'froth_speed': 'speed_mean',  # 平均速度
            'froth_stability': 'stability',  # 稳定性
            'froth_red_gray_ratio': 'color_red_gray_ratio',  # 红灰比 (关键氧化程度指标)
            'froth_gray_mean': 'color_gray_mean',  # 灰度均值 (亮度)
            'froth_entropy': 'lbp_entropy',  # 纹理熵 (表面粗糙度)

            # --- [新增] 颜色特征 (RGB & HSV) ---
            'froth_r_mean': 'color_r_mean',  # R分量
            'froth_g_mean': 'color_g_mean',  # G分量
            'froth_b_mean': 'color_b_mean',  # B分量
            'froth_h_mean': 'color_h_mean',  # 色调 (Hue)
            'froth_s_mean': 'color_s_mean',  # 饱和度 (Saturation)
            'froth_v_mean': 'color_v_mean',  # 亮度 (Value)

            # --- [新增] 颜色统计矩 (反映颜色分布一致性) ---
            'froth_color_var': 'color_variance',  # 颜色方差
            'froth_color_skew': 'color_skewness',  # 颜色偏度
            'froth_color_kurt': 'color_kurtosis',  # 颜色峰度

            # --- [新增] 纹理特征 (GLCM - 反映泡沫细腻程度) ---
            'froth_glcm_contrast': 'glcm_contrast',  # 对比度
            'froth_glcm_energy': 'glcm_energy',  # 能量 (一致性)
            'froth_glcm_corr': 'glcm_correlation',  # 相关性
            'froth_glcm_homo': 'glcm_homogeneity',  # 同质性

            # --- [新增] 形态学分布 (反映大小不均程度) ---
            'froth_d10': 'bubble_d10',  # 10% 粒径
            'froth_d50': 'bubble_d50',  # 中值粒径 (比平均值更鲁棒)
            'froth_d90': 'bubble_d90',  # 90% 粒径 (反映大泡占比)
            'froth_circularity': 'bubble_mean_circularity',  # 圆度 (反映兼并/破裂程度)
            'froth_mean_area': 'bubble_mean_area',  # 平均面积

            # --- [新增] 动态特征 ---
            'froth_speed_var': 'speed_variance'  # 速度方差 (反映流动是否紊乱)
        }

        # 加载外部定义的其他标签
        self.all_csv_headers = self._load_all_headers()
        # [修改] 构建全量固定表头
        # 逻辑：Timestamp + 相机ID + (药剂Tag + 品位Tag + 泡沫Key) + 外部文件Tag
        # 重点：通过 values() 获取原始的 Key/Tag，确保 _save_to_csv 能在 flat_data 中找到对应值
        important_keys = list(self.reagent_mapping.values()) + \
                         list(self.grade_mapping.values()) + \
                         list(self.froth_mapping.values())

        # 合并并去重
        self.fixed_csv_headers = ["Timestamp", "camera_id"] + \
                                 sorted(list(set(important_keys + self.all_csv_headers)))
        self.last_periodic_save_time = datetime.min
        self.yj_value_cache = {}

    def start(self) -> bool:
        try:
            self.status = ServiceStatus.STARTING
            self._init_database()
            self.status = ServiceStatus.RUNNING
            return True
        except Exception as e:
            self.status = ServiceStatus.ERROR
            raise ServiceError(f"数据服务启动失败: {e}")

    def stop(self) -> bool:
        self.status = ServiceStatus.STOPPED
        return True

    def restart(self) -> bool:
        self.stop()
        return self.start()

    def _load_all_headers(self) -> List[str]:
        """加载CSV表头"""
        headers = []
        try:
            if os.path.exists(self.tag_list_file):
                with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if not row: continue
                        raw = row[0]
                        if "source:" in raw: raw = raw.split(']')[-1]
                        cleaned = re.sub(r'[\[\]]', '', raw).strip()
                        if cleaned.startswith('yj_'):
                            tag = f'YJ.{cleaned}'
                        elif cleaned.startswith('kyfx_'):
                            tag = f'KYFX.{cleaned}'
                        else:
                            tag = cleaned
                        headers.append(tag)
        except Exception as e:
            print(f"加载标签列表失败: {e}")
        return headers

    def _init_database(self) -> None:
        """初始化数据库：自动创建表和添加缺失的列"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 1. 基础建表语句 (含药剂列)
            reagent_sql = ""
            for col in self.reagent_mapping.keys():
                reagent_sql += f",\n                             {col} REAL"

            # 注意：首次建表时不包含 froth_columns，依靠下方的 ALTER 逻辑统一添加
            cursor.execute(f'''
                 CREATE TABLE IF NOT EXISTS process_history
                 (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp DATETIME NOT NULL,
                     feed_grade REAL,
                     conc_grade REAL,
                     recovery REAL{reagent_sql},
                     raw_data JSON
                 )
            ''')

            # 2. 获取现有列名
            cursor.execute("PRAGMA table_info(process_history)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # 3. 辅助函数：添加缺失列
            def add_missing_columns(mapping):
                for col_name in mapping.keys():
                    if col_name not in existing_columns:
                        try:
                            cursor.execute(f"ALTER TABLE process_history ADD COLUMN {col_name} REAL")
                            print(f"[DataService] 自动添加新列: {col_name}")
                        except Exception as e:
                            print(f"添加列 {col_name} 失败: {e}")

            # 4. 检查并添加 药剂列 和 泡沫特征列
            add_missing_columns(self.reagent_mapping)
            add_missing_columns(self.froth_mapping)

            # 5. 确保 raw_data 存在
            if 'raw_data' not in existing_columns:
                cursor.execute("ALTER TABLE process_history ADD COLUMN raw_data JSON")

            conn.commit()

    def record_data(self, data: Dict[str, Any]) -> None:
        """接收并缓存数据，满足条件时写入存储"""
        try:
            timestamp = datetime.now()
            should_save = False

            with self._cache_lock:
                self._cache.update(data)
                self._cache['last_updated'] = timestamp

            # 获取保存间隔 (默认为1秒，适应实时性)
            try:
                slow_interval = config_manager.get_network_config().slow_tag_interval
                if slow_interval < 1.0: slow_interval = 1.0  # 限制最小间隔
            except:
                slow_interval = 1.0

            # 策略1: 定时保存
            if (timestamp - self.last_periodic_save_time).total_seconds() >= slow_interval:
                should_save = True
                self.last_periodic_save_time = timestamp

            # 策略2: 药剂值变化触发
            if not should_save:
                for key, val_dict in data.items():
                    if key.startswith("YJ."):
                        val = val_dict.get('value')
                        if self.yj_value_cache.get(key) != val:
                            self.yj_value_cache[key] = val
                            should_save = True
                            break

            if should_save:
                # 展平数据用于存储 (处理 {value: x} 格式)
                flat_data = {}
                for key, val in self._cache.items():
                    if isinstance(val, dict) and 'value' in val:
                        v = val['value']
                        flat_data[key] = float(v) if v is not None else 0.0
                    else:
                        flat_data[key] = val

                self._save_to_sqlite(timestamp, flat_data)
                self._save_to_csv(timestamp, flat_data)

        except Exception as e:
            print(f"数据保存流程异常: {e}")

    def _save_to_sqlite(self, timestamp, flat_data: Dict[str, Any]):
        """将缓存数据写入 SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            def get_val(key, default=0.0):
                v = flat_data.get(key)
                if v is None or v == -9999.0: return default
                try:
                    return float(v)
                except:
                    return default

            # --- 1. 核心指标 (使用映射获取) ---
            # 直接使用 grade_mapping 中的 Tag 来取值
            f = get_val(self.grade_mapping['feed_grade_Pb'])
            c = get_val(self.grade_mapping['conc_grade_Pb'])
            c_total = get_val(self.grade_mapping['conc_total_Pb'])
            t = get_val(self.grade_mapping['tail_grade_Pb'])

            # 计算回收率
            rec = 0.0
            if f > 0 and (c_total - t) != 0:
                rec = (c_total * (f - t)) / (f * (c_total - t)) * 100

            columns = ['timestamp', 'feed_grade', 'conc_grade', 'recovery']
            values = [timestamp, f, c, rec]

            # --- 2. 药剂数据 ---
            for col_name, tag_name in self.reagent_mapping.items():
                columns.append(col_name)
                values.append(get_val(tag_name))

            # --- 3. 泡沫特征数据 ---
            for col_name, dict_key in self.froth_mapping.items():
                columns.append(col_name)
                values.append(get_val(dict_key))

            # --- 4. 原始 JSON ---
            columns.append('raw_data')
            values.append(json.dumps(flat_data, default=str))

            # --- 执行插入 ---
            placeholders = ', '.join(['?'] * len(columns))
            sql = f'INSERT INTO process_history ({", ".join(columns)}) VALUES ({placeholders})'

            cursor.execute(sql, values)
            conn.commit()

    def _save_to_csv(self, timestamp, flat_data: Dict[str, Any]):
        """保存 CSV 备份 (修复版：使用固定表头)"""
        try:
            filename = f"{timestamp.strftime('%Y%m%d')}_process_data.csv"
            filepath = self.csv_dir / filename
            file_exists = filepath.exists()

            with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # [修改] 不再使用 flat_data.keys()，而是使用 self.fixed_csv_headers
                # 这样即使第一帧没有分析数据，表头也会包含 'bubble_mean_diam' 等列
                if not file_exists:
                    writer.writerow(self.fixed_csv_headers)

                # [修改] 根据固定表头构建数据行，确保列对齐
                row = []
                for key in self.fixed_csv_headers:
                    if key == "Timestamp":
                        row.append(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                    elif key == "camera_id":
                        # 特殊处理相机ID，如果缓存里是 camera_index
                        row.append(flat_data.get('camera_index', ''))
                    else:
                        # 如果缓存里还没有这个数据（例如分析还没算完），填空字符串或0
                        row.append(flat_data.get(key, ""))

                writer.writerow(row)
        except Exception as e:
            print(f"CSV保存失败: {e}")

    def get_current_data(self, key: Optional[str] = None) -> Any:
        with self._cache_lock:
            if key: return self._cache.get(key)
            return self._cache.copy()

    def get_historical_data(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """查询历史数据，返回字典列表"""
        if not os.path.exists(self.db_path):
            return []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 动态构建 SELECT 语句，包含所有映射的列
            reagent_cols = ", ".join(self.reagent_mapping.keys())
            froth_cols = ", ".join(self.froth_mapping.keys())

            # 组合 SQL
            sql = f'''
               SELECT timestamp, feed_grade, conc_grade, recovery, 
                      {reagent_cols}, {froth_cols}, raw_data
               FROM process_history
               WHERE timestamp BETWEEN ? AND ?
               ORDER BY timestamp DESC
            '''

            try:
                cursor.execute(sql, (start_time, end_time))
                return [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                # 如果因为列不存在导致查询失败，返回空（可能正在初始化）
                return []


# 单例模式
_data_service_instance = None


def get_data_service() -> DataService:
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance

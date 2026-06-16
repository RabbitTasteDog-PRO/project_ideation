# -- API 캐시 실행 이력 테이블
CREATE TABLE IF NOT EXISTS api_cache_runs
(
    id                    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '캐시 실행 ID',

    region_name           VARCHAR(50)     NOT NULL COMMENT '조회 지역명',

    selected_district     VARCHAR(100)    NULL COMMENT '선택한 시군구',

    selected_neighborhood VARCHAR(100)    NULL COMMENT '선택한 읍면동',

    fetched_at            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '데이터 조회 시각',

    expires_at            DATETIME        NOT NULL COMMENT '캐시 만료 시각',

    charger_count         INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '저장된 충전기 수',

    PRIMARY KEY (id) COMMENT '캐시 실행 기본 키',

    INDEX idx_cache_lookup (
                            region_name,
                            expires_at
        ) COMMENT '지역명과 만료 시각 기준 캐시 조회 인덱스'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
    COMMENT ='API 캐시 실행 정보';

# -- 충전기 스냅샷 테이블
CREATE TABLE IF NOT EXISTS charger_snapshots
(
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '스냅샷 ID',

    cache_run_id BIGINT UNSIGNED NOT NULL COMMENT '캐시 실행 ID',

    stat_id      VARCHAR(50)     NOT NULL COMMENT '충전소 ID',

    chger_id     VARCHAR(20)     NOT NULL COMMENT '충전기 ID',

    stat_nm      VARCHAR(255)    NULL COMMENT '충전소명',

    addr         VARCHAR(500)    NULL COMMENT '충전소 주소',

    lat          DECIMAL(10, 7)  NULL COMMENT '위도',

    lng          DECIMAL(10, 7)  NULL COMMENT '경도',

    output       DECIMAL(8, 2)   NULL COMMENT '충전 용량(kW)',

    stat         VARCHAR(10)     NULL COMMENT '충전기 상태: 1 통신 이상, 2 충전 대기, 3 충전 중, 4 운영 중지, 5 점검 중, 9 상태 미확인',

    PRIMARY KEY (id) COMMENT '스냅샷 기본 키',

    CONSTRAINT fk_charger_snapshots_cache_run
        FOREIGN KEY (cache_run_id)
            REFERENCES api_cache_runs (id)
            ON DELETE CASCADE,

    UNIQUE KEY uq_charger_snapshot (
                                    cache_run_id,
                                    stat_id,
                                    chger_id
        ) COMMENT '같은 캐시 실행 내 동일 충전기 중복 방지',

    INDEX idx_charger_status (stat) COMMENT '충전기 상태별 조회 인덱스',

    INDEX idx_charger_station (stat_id) COMMENT '충전소별 조회 인덱스',

    INDEX idx_charger_output (output) COMMENT '충전 용량별 조회 인덱스'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
    COMMENT ='전기차 충전기 상태 스냅샷';



# -- API 캐시 실행 이력 테이블
# CREATE TABLE `api_cache_runs` (
#     `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '캐시 실행 고유 ID',
#     `cache_type` VARCHAR(50) NOT NULL COMMENT '캐시 유형',
#     `region_code` VARCHAR(10) NOT NULL COMMENT '지역 코드',
#     `region_name` VARCHAR(50) NOT NULL COMMENT '지역명',
#     `selected_district` VARCHAR(100) NULL COMMENT '선택한 시군구',
#     `selected_neighborhood` VARCHAR(100) NULL COMMENT '선택한 읍면동',
#     `fetched_at` DATETIME NOT NULL COMMENT 'API 조회 시각',
#     `expires_at` DATETIME NOT NULL COMMENT '캐시 만료 시각',
#     `info_count` INT NOT NULL DEFAULT 0 COMMENT '충전소 정보 건수',
#     `status_count` INT NOT NULL DEFAULT 0 COMMENT '충전기 상태 건수',
#     `merged_count` INT NOT NULL DEFAULT 0 COMMENT '병합 데이터 건수',
#     `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일'
# );
#
# -- 충전기 스냅샷 테이블
# CREATE TABLE `charger_snapshots` (
#     `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '충전기 스냅샷 고유 ID',
#     `cache_run_id` BIGINT NOT NULL COMMENT '캐시 실행 ID',
#
#     `stat_id` VARCHAR(50) NOT NULL COMMENT '충전소 ID',
#     `chger_id` VARCHAR(20) NOT NULL COMMENT '충전기 ID',
#
#     `stat_nm` VARCHAR(255) NULL COMMENT '충전소명',
#     `chger_type` VARCHAR(20) NULL COMMENT '충전기 타입',
#
#     `addr` VARCHAR(500) NULL COMMENT '주소',
#     `addr_detail` VARCHAR(500) NULL COMMENT '상세 주소',
#     `location` VARCHAR(255) NULL COMMENT '설치 위치',
#
#     `lat` DECIMAL(10,7) NULL COMMENT '위도',
#     `lng` DECIMAL(10,7) NULL COMMENT '경도',
#
#     `use_time` VARCHAR(255) NULL COMMENT '이용 가능 시간',
#
#     `busi_id` VARCHAR(50) NULL COMMENT '운영기관 ID',
#     `busi_nm` VARCHAR(255) NULL COMMENT '운영기관명',
#     `busi_call` VARCHAR(100) NULL COMMENT '운영기관 연락처',
#
#     `output` DECIMAL(8,2) NULL COMMENT '충전 출력(kW)',
#     `method` VARCHAR(100) NULL COMMENT '충전 방식',
#
#     `zcode` VARCHAR(10) NULL COMMENT '지역 코드',
#     `zscode` VARCHAR(20) NULL COMMENT '상세 지역 코드',
#
#     `kind` VARCHAR(20) NULL COMMENT '충전소 구분',
#     `kind_detail` VARCHAR(20) NULL COMMENT '충전소 상세 구분',
#
#     `parking_free` VARCHAR(10) NULL COMMENT '주차 무료 여부',
#     `note` TEXT NULL COMMENT '비고',
#
#     `limit_yn` VARCHAR(10) NULL COMMENT '이용 제한 여부',
#     `limit_detail` VARCHAR(500) NULL COMMENT '이용 제한 상세 정보',
#
#     `stat` VARCHAR(10) NULL COMMENT '충전기 상태 코드',
#     `stat_upd_dt` VARCHAR(20) NULL COMMENT '상태 갱신 시각',
#
#     `district` VARCHAR(100) NULL COMMENT '시군구',
#     `neighborhood` VARCHAR(100) NULL COMMENT '읍면동',
#
#     `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일'
# );
#
# -- =====================
# -- PRIMARY KEY
# -- =====================
#
# ALTER TABLE `api_cache_runs`
# ADD CONSTRAINT `PK_API_CACHE_RUNS`
# PRIMARY KEY (`id`);
#
# ALTER TABLE `charger_snapshots`
# ADD CONSTRAINT `PK_CHARGER_SNAPSHOTS`
# PRIMARY KEY (`id`);
#
# -- =====================
# -- FOREIGN KEY
# -- =====================
#
# ALTER TABLE `charger_snapshots`
# ADD CONSTRAINT `FK_CHARGER_SNAPSHOTS_CACHE_RUN`
# FOREIGN KEY (`cache_run_id`)
# REFERENCES `api_cache_runs` (`id`)
# ON DELETE CASCADE;
#
# -- =====================
# -- UNIQUE KEY
# -- =====================
#
# ALTER TABLE `charger_snapshots`
# ADD CONSTRAINT `UQ_CHARGER_SNAPSHOT`
# UNIQUE (
#     `cache_run_id`,
#     `stat_id`,
#     `chger_id`
# );
#
# -- =====================
# -- INDEX
# -- =====================
#
# CREATE INDEX `IDX_API_CACHE_RUNS_LOOKUP`
# ON `api_cache_runs`
# (
#     `cache_type`,
#     `region_code`,
#     `expires_at`
# );
#
# CREATE INDEX `IDX_API_CACHE_RUNS_SELECTION`
# ON `api_cache_runs`
# (
#     `cache_type`,
#     `region_code`,
#     `selected_district`,
#     `selected_neighborhood`
# );
#
# CREATE INDEX `IDX_API_CACHE_RUNS_FETCHED_AT`
# ON `api_cache_runs`
# (
#     `fetched_at`
# );
#
# CREATE INDEX `IDX_CHARGER_LOCATION`
# ON `charger_snapshots`
# (
#     `zcode`,
#     `district`,
#     `neighborhood`
# );
#
# CREATE INDEX `IDX_CHARGER_STATUS`
# ON `charger_snapshots`
# (
#     `stat`
# );
#
# CREATE INDEX `IDX_CHARGER_STATION`
# ON `charger_snapshots`
# (
#     `stat_id`
# );
#
# CREATE INDEX `IDX_CHARGER_OUTPUT`
# ON `charger_snapshots`
# (
#     `output`
# );
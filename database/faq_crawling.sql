CREATE TABLE IF NOT EXISTS ev_user_questions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '질문 고유 ID',

    source_name VARCHAR(100) NOT NULL DEFAULT '클리앙' COMMENT '수집 사이트명',

    category VARCHAR(100) NULL COMMENT '게시판명 또는 카테고리명',

    title VARCHAR(500) NOT NULL COMMENT '게시글 제목',

    content TEXT NULL COMMENT '게시글 본문',

    url VARCHAR(1000) NOT NULL COMMENT '원본 게시글 URL',

    published_at VARCHAR(50) NULL COMMENT '게시글 작성일',

    view_count INT UNSIGNED NULL COMMENT '게시글 조회수',

    comment_count INT UNSIGNED NULL COMMENT '게시글 댓글 수',

    collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '데이터 수집 시각',

    PRIMARY KEY (id) COMMENT '질문 테이블 기본 키',

    UNIQUE KEY uq_ev_user_questions_url (
        url
    ) COMMENT '원본 URL 기준 중복 저장 방지',

    INDEX idx_ev_user_questions_source (
        source_name
    ) COMMENT '수집 사이트별 조회 인덱스',

    INDEX idx_ev_user_questions_published_at (
        published_at
    ) COMMENT '작성일 기준 조회 인덱스',

    INDEX idx_ev_user_questions_collected_at (
        collected_at
    ) COMMENT '수집일 기준 조회 인덱스'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='전기차 사용자 질문 크롤링 데이터';

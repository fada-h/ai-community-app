-- =====================================================================
-- 青禾 · AI 校园社区 —— MySQL 8.0 建表脚本
-- 说明：应用启动时会通过 SQLAlchemy 自动建表；本文件用于手动建库、
--       数据库设计评审或比赛材料提交。
-- 字符集：utf8mb4 / utf8mb4_unicode_ci
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `campus_ai_community`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `campus_ai_community`;

-- 用户
CREATE TABLE IF NOT EXISTS `users` (
  `id`            INT AUTO_INCREMENT PRIMARY KEY,
  `username`      VARCHAR(32)  NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `nickname`      VARCHAR(32)  NOT NULL DEFAULT '',
  `avatar`        VARCHAR(8)   NOT NULL DEFAULT '🌱',
  `color`         VARCHAR(16)  NOT NULL DEFAULT '#0f766e',
  `major`         VARCHAR(50)  NOT NULL DEFAULT '',
  `grade`         VARCHAR(16)  NOT NULL DEFAULT '',
  `bio`           VARCHAR(300) NOT NULL DEFAULT '',
  `tags`          JSON         NULL,
  `is_admin`      TINYINT(1)   NOT NULL DEFAULT 0,
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_users_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 帖子
CREATE TABLE IF NOT EXISTS `posts` (
  `id`         INT AUTO_INCREMENT PRIMARY KEY,
  `author_id`  INT          NOT NULL,
  `category`   VARCHAR(16)  NOT NULL,
  `title`      VARCHAR(80)  NOT NULL,
  `content`    TEXT         NOT NULL,
  `tags`       JSON         NULL,
  `views`      INT          NOT NULL DEFAULT 0,
  `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_posts_author` (`author_id`),
  KEY `idx_posts_category` (`category`),
  KEY `idx_posts_created` (`created_at`),
  CONSTRAINT `fk_posts_author` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 评论
CREATE TABLE IF NOT EXISTS `comments` (
  `id`         INT AUTO_INCREMENT PRIMARY KEY,
  `post_id`    INT          NOT NULL,
  `author_id`  INT          NOT NULL,
  `content`    VARCHAR(500) NOT NULL,
  `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_comments_post` (`post_id`),
  CONSTRAINT `fk_comments_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_comments_author` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 点赞
CREATE TABLE IF NOT EXISTS `post_likes` (
  `id`         INT AUTO_INCREMENT PRIMARY KEY,
  `post_id`    INT      NOT NULL,
  `user_id`    INT      NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_post_like` (`post_id`, `user_id`),
  CONSTRAINT `fk_likes_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AI 搭子匹配记录
CREATE TABLE IF NOT EXISTS `match_records` (
  `id`             INT AUTO_INCREMENT PRIMARY KEY,
  `user_id`        INT          NOT NULL,
  `target_user_id` INT          NOT NULL,
  `score`          FLOAT        NOT NULL DEFAULT 0,
  `reason`         VARCHAR(300) NOT NULL DEFAULT '',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 私信
CREATE TABLE IF NOT EXISTS `messages` (
  `id`          INT AUTO_INCREMENT PRIMARY KEY,
  `sender_id`   INT           NOT NULL,
  `receiver_id` INT           NOT NULL,
  `content`     VARCHAR(1000) NOT NULL,
  `is_read`     TINYINT(1)    NOT NULL DEFAULT 0,
  `created_at`  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_messages_pair` (`sender_id`, `receiver_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AI 调用日志
CREATE TABLE IF NOT EXISTS `ai_logs` (
  `id`         INT AUTO_INCREMENT PRIMARY KEY,
  `user_id`    INT         NOT NULL DEFAULT 0,
  `kind`       VARCHAR(16) NOT NULL,
  `input`      VARCHAR(200) NOT NULL DEFAULT '',
  `mode`       VARCHAR(16) NOT NULL DEFAULT 'local',
  `chars`      INT         NOT NULL DEFAULT 0,
  `created_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

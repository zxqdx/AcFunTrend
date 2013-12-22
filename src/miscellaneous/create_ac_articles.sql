CREATE DATABASE  IF NOT EXISTS `trend_acws` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;
USE `trend_acws`;
-- MySQL dump 10.13  Distrib 5.6.11, for Win32 (x86)
--
-- Host: localhost    Database: trend_acws
-- ------------------------------------------------------
-- Server version	5.6.13

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ac_articles`
--

DROP TABLE IF EXISTS `ac_articles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ac_articles` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` varchar(1024) NOT NULL,
  `user_id` int(11) NOT NULL,
  `user_name` varchar(255) NOT NULL,
  `sort_time` bigint(20) NOT NULL,
  `sort_time_day` int(11) NOT NULL,
  `sort_time_ac_day` int(11) NOT NULL,
  `sort_time_week` int(11) NOT NULL,
  `sort_time_month` int(11) NOT NULL,
  `sort_time_year` int(11) NOT NULL,
  `last_feed_back_time` bigint(20) NOT NULL,
  `img` varchar(255) NOT NULL,
  `content_img` varchar(255) NOT NULL,
  `views` bigint(20) NOT NULL,
  `week_views` int(11) NOT NULL,
  `month_views` int(11) NOT NULL,
  `day_views` int(11) NOT NULL,
  `comments` int(11) NOT NULL,
  `stows` int(11) NOT NULL,
  `score` int(11) NOT NULL,
  `score_trend` int(11) NOT NULL,
  `channel_name` varchar(255) NOT NULL,
  `channel_id` int(11) NOT NULL,
  `tags` text NOT NULL,
  `time_video` int(11) DEFAULT NULL,
  `survive` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `sort_time` (`sort_time`),
  KEY `sort_date` (`sort_time_day`,`sort_time_month`,`sort_time_year`),
  KEY `sort_week` (`sort_time_week`),
  KEY `views` (`views`),
  KEY `comments` (`comments`),
  KEY `stows` (`stows`),
  KEY `score` (`score`),
  KEY `score_trend` (`score_trend`),
  KEY `time_video` (`time_video`),
  KEY `sort_day` (`sort_time_ac_day`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-12-22  5:43:27

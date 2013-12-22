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
-- Table structure for table `ac_users`
--

DROP TABLE IF EXISTS `ac_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ac_users` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `hits` bigint(20) NOT NULL,
  `comments` bigint(20) NOT NULL,
  `stows` bigint(20) NOT NULL,
  `score` bigint(20) NOT NULL,
  `score_trend` bigint(20) NOT NULL,
  `contains` int(11) NOT NULL,
  `register_time` bigint(20) DEFAULT NULL,
  `rank` int(11) DEFAULT NULL,
  `gender` int(11) DEFAULT NULL,
  `sex_trend` int(11) DEFAULT NULL,
  `come_from` varchar(255) DEFAULT NULL,
  `img` varchar(255) DEFAULT NULL,
  `last_login_time` bigint(20) DEFAULT NULL,
  `online_duration` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `rank` (`rank`),
  KEY `hits` (`hits`),
  KEY `comments` (`comments`),
  KEY `stows` (`stows`),
  KEY `score` (`score`),
  KEY `score_trend` (`score_trend`),
  KEY `contains` (`contains`),
  KEY `online_duration` (`online_duration`)
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

-- Dump completed on 2013-12-21 17:43:26

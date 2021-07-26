-- MySQL dump 10.13  Distrib 5.7.34, for Linux (x86_64)
--
-- Host: localhost    Database: trade
-- ------------------------------------------------------
-- Server version	5.7.34

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
-- Table structure for table `bn_data`
--

DROP TABLE IF EXISTS `bn_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bn_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ntime` varchar(100) DEFAULT NULL,
  `cyPair` varchar(100) DEFAULT NULL,
  `open` varchar(100) DEFAULT NULL,
  `close` varchar(100) DEFAULT NULL,
  `low` varchar(100) DEFAULT NULL,
  `high` varchar(100) DEFAULT NULL,
  `amount` varchar(100) DEFAULT NULL,
  `volume` varchar(100) DEFAULT NULL,
  `count` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `key_balance`
--

DROP TABLE IF EXISTS `key_balance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `key_balance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(50) DEFAULT NULL,
  `this_time` varchar(50) DEFAULT NULL,
  `balance` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `key_table`
--

DROP TABLE IF EXISTS `key_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `key_table` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(100) DEFAULT NULL,
  `access_key` varchar(100) DEFAULT NULL,
  `secret_key` varchar(100) DEFAULT NULL,
  `pass_phrase` varchar(100) DEFAULT NULL,
  `stime` varchar(50) DEFAULT NULL,
  `pwd` varchar(50) DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `index_name` (`user_name`)
) ENGINE=InnoDB AUTO_INCREMENT=137 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sign_bn`
--

DROP TABLE IF EXISTS `sign_bn`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sign_bn` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `strategy` varchar(30) DEFAULT NULL,
  `signal` varchar(30) DEFAULT NULL,
  `target_one` varchar(30) DEFAULT NULL,
  `target_two` varchar(30) DEFAULT NULL,
  `target_one2` varchar(30) DEFAULT NULL,
  `target_two2` varchar(30) DEFAULT NULL,
  `ntime` varchar(30) DEFAULT NULL,
  `status` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12492 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-07-26 17:31:05

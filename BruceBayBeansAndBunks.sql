-- MySQL dump 10.13  Distrib 8.0.34, for Win64 (x86_64)
--
-- Host: localhost    Database: brucebaybeansandbunks
-- ------------------------------------------------------
-- Server version	8.0.35
-- Drop the existing database
drop database if exists brucebaybeansandbunks;
create database brucebaybeansandbunks;
use brucebaybeansandbunks;
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accommodationavailability`
--

DROP TABLE IF EXISTS `accommodationavailability`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accommodationavailability` (
  `availabilityid` int NOT NULL AUTO_INCREMENT,
  `accommodationid` int DEFAULT NULL,
  `date` date DEFAULT NULL,
  `availablerooms` int DEFAULT NULL,
  PRIMARY KEY (`availabilityid`),
  KEY `accommodationid` (`accommodationid`),
  CONSTRAINT `accommodationavailability_ibfk_1` FOREIGN KEY (`accommodationid`) REFERENCES `accommodations` (`accommodationid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accommodationavailability`
--

LOCK TABLES `accommodationavailability` WRITE;
/*!40000 ALTER TABLE `accommodationavailability` DISABLE KEYS */;
INSERT INTO `accommodationavailability` (`availabilityid`, `accommodationid`, `date`, `availablerooms`) VALUES
(1, 1, '2024-07-01', 4),  -- Dorm Room
(2, 2, '2024-07-02', 3),  -- Queen Room
(3, 3, '2024-07-03', 2);  -- Twin Room
/*!40000 ALTER TABLE `accommodationavailability` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accommodations`
--

DROP TABLE IF EXISTS `accommodations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accommodations` (
  `accommodationid` int NOT NULL AUTO_INCREMENT,
  `productid` int DEFAULT NULL,
  `numberavailable` int DEFAULT NULL,
  `maxcapacity` int DEFAULT NULL,
  `image` varchar(255) DEFAULT NULL,
  `availabilityid` int DEFAULT NULL,
  `room_type` varchar(50) DEFAULT NULL,  -- New column for room type
  PRIMARY KEY (`accommodationid`),
  KEY `productid` (`productid`),
  CONSTRAINT `accommodations_ibfk_1` FOREIGN KEY (`productid`) REFERENCES `products` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accommodations`
--

LOCK TABLES `accommodations` WRITE;
/*!40000 ALTER TABLE `accommodations` DISABLE KEYS */;
INSERT INTO `accommodations` (`accommodationid`, `productid`, `numberavailable`, `maxcapacity`, `image`, `availabilityid`, `room_type`) VALUES
(1, 16, 4, 4, 'dorm_room1.png', 1, 'dorm'),  -- Dorm Room
(2, 17, 3, 3, 'queen_room.jpg', 2, 'queen'),  -- Queen Room
(3, 18, 2, 2, 'DSC_1503ok.jpg', 3, 'twin');  -- Twin Room
/*!40000 ALTER TABLE `accommodations` ENABLE KEYS */;
UNLOCK TABLES;
--
-- Table structure for table `bookings`
--

-- Table structure for table `bookings`
DROP TABLE IF EXISTS `bookings`;
CREATE TABLE `bookings` (
  `bookingid` int NOT NULL AUTO_INCREMENT,
  `customerid` int DEFAULT NULL,
  `accommodationid` int DEFAULT NULL,
  `checkindate` date DEFAULT NULL,
  `checkoutdate` date DEFAULT NULL,
  `status` enum('booked','cancelled','completed') DEFAULT NULL,
  `num_beds` int DEFAULT 1,
  `booking_reference` varchar(255) DEFAULT NULL,
  `total_cost` DECIMAL(10, 2) NOT NULL,
  PRIMARY KEY (`bookingid`),
  KEY `customerid` (`customerid`),
  KEY `accommodationid` (`accommodationid`),
  CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`),
  CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`accommodationid`) REFERENCES `accommodations` (`accommodationid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bookings`
--
-- Insert existing data with `num_beds` and `total_cost` columns
LOCK TABLES `bookings` WRITE;
/*!40000 ALTER TABLE `bookings` DISABLE KEYS */;
INSERT INTO `bookings` (`bookingid`, `customerid`, `accommodationid`, `checkindate`, `checkoutdate`, `status`, `num_beds`, `booking_reference`, `total_cost`) VALUES 
(1, 1, 1, '2024-06-01', '2024-06-02', 'booked', 2, 'BR1', 100.00),
(2, 2, 2, '2024-06-03', '2024-06-04', 'cancelled', 1, 'BR2', 150.00),
(3, 3, 3, '2024-06-05', '2024-06-06', 'booked', 1, 'BR3', 200.00),
(4, 4, 2, '2024-06-07', '2024-06-08', 'booked', 1, 'BR4', 250.00),
(5, 5, 3, '2024-06-09', '2024-06-10', 'cancelled', 1, 'BR5', 300.00);
/*!40000 ALTER TABLE `bookings` ENABLE KEYS */;
UNLOCK TABLES;


CREATE TABLE blocked_dates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    accommodationid INT NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (accommodationid) REFERENCES accommodations(accommodationid)
);

-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customers` (
  `customerid` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `firstname` varchar(255) NOT NULL,
  `lastname` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phonenumber` varchar(20) DEFAULT NULL,
  `createdat` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `lastlogin` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`customerid`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customers`
--

LOCK TABLES `customers` WRITE;
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
INSERT INTO `customers` VALUES (1,'emmasmith','emma','smith','emma.smith@example.com','021211121','2024-05-26 11:59:49',NULL),(2,'liamjones','liam','jones','liam.jones@example.com','123-456-7891','2024-05-26 11:59:49',NULL),(3,'oliviabrown','olivia','brown','olivia.brown@example.com','123-456-7892','2024-05-26 11:59:49',NULL),(4,'noahwilson','noah','wilson','noah.wilson@example.com','123-456-7893','2024-05-26 11:59:49',NULL),(5,'avadavis','ava','davis','ava.davis@example.com','123-456-7894','2024-05-26 11:59:49',NULL);
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `giftcard`
--

DROP TABLE IF EXISTS `giftcard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `giftcard` (
  `giftcardid` int NOT NULL AUTO_INCREMENT,
  `customerid` int DEFAULT NULL,
  `amount` decimal(10,2) NOT NULL,
  `isactive` tinyint(1) DEFAULT '1',
  `expirydate` date DEFAULT NULL,
  `createdat` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`giftcardid`),
  KEY `customerid` (`customerid`),
  CONSTRAINT `giftcard_ibfk_1` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `giftcard`
--

LOCK TABLES `giftcard` WRITE;
/*!40000 ALTER TABLE `giftcard` DISABLE KEYS */;
INSERT INTO `giftcard` VALUES (1,1,50.00,1,'2025-12-31','2024-05-26 11:59:49'),(2,2,100.00,1,'2025-12-31','2024-05-26 11:59:49'),(3,3,25.00,1,'2025-12-31','2024-05-26 11:59:49'),(4,4,75.00,1,'2025-12-31','2024-05-26 11:59:49'),(5,5,200.00,1,'2025-12-31','2024-05-26 11:59:49');
/*!40000 ALTER TABLE `giftcard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory`
--

DROP TABLE IF EXISTS `inventory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory` (
  `productid` int NOT NULL,
  `quantityavailable` int DEFAULT NULL,
  `lowstockthreshold` int DEFAULT NULL,
  `alert_sent` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`productid`),
  CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`productid`) REFERENCES `products` (`productid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

-- Dumping data for table `inventory`
--

LOCK TABLES `inventory` WRITE;
/*!40000 ALTER TABLE `inventory` DISABLE KEYS */;
INSERT INTO `inventory` VALUES 
(1, 82, 10, 0),
(2, 25, 15, 0),
(3, 50, 5, 0),
(4, 30, 4, 0),
(5, 20, 2, 0),
(6, 100, 10, 0),  -- Coffee
(7, 80, 20, 0),  -- Soft Drink
(8, 60, 10, 0),  -- Milkshake
(9, 70, 15, 0),  -- Iced Tea
(10, 40, 5, 0),  -- American Hotdog
(11, 35, 7, 0),  -- Sweetcorn & Kumara Patties
(12, 50, 8, 0),  -- Crepes
(13, 45, 10, 0), -- Smokey BBQ Pulled Pork in a Bun
(14, 90, 20, 0), -- Muffin
(15, 85, 15, 0), -- Slice
(16, 100, 25, 0),-- Ice Block
(17, 75, 12, 0); -- Real Fruit Ice Cream
/*!40000 ALTER TABLE `inventory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `managers`
--

DROP TABLE IF EXISTS `managers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `managers` (
  `managerid` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `passwordhash` varchar(255) NOT NULL,
  `createdat` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `lastlogin` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`managerid`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `managers`
--

LOCK TABLES `managers` WRITE;
/*!40000 ALTER TABLE `managers` DISABLE KEYS */;
INSERT INTO `managers` VALUES (1,'alicecooper','alice.cooper@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL),(2,'bobmarley','bob.marley@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL),(3,'charliechaplin','charlie.chaplin@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL),(4,'dianaross','diana.ross@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL),(5,'elvispresley','elvis.presley@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL);
/*!40000 ALTER TABLE `managers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `messageid` int NOT NULL AUTO_INCREMENT,
  `senderid` int DEFAULT NULL,
  `receiverid` int DEFAULT NULL,
  `sendertype` enum('customer','staff','manager') DEFAULT NULL,
  `receivertype` enum('customer','staff','manager') DEFAULT NULL,
  `content` text,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`messageid`),
  KEY `senderid` (`senderid`),
  KEY `receiverid` (`receiverid`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`senderid`) REFERENCES `customers` (`customerid`),
  CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`receiverid`) REFERENCES `staff` (`staffid`),
  CONSTRAINT `messages_ibfk_3` FOREIGN KEY (`receiverid`) REFERENCES `managers` (`managerid`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
INSERT INTO `messages` VALUES (1,1,1,'customer','staff','can i have an extra pillow?','2024-05-26 11:59:49'),(2,2,2,'customer','staff','can i check in early?','2024-05-26 11:59:49'),(3,3,3,'customer','staff','can i get a late checkout?','2024-05-26 11:59:49'),(4,4,4,'customer','staff','is breakfast included?','2024-05-26 11:59:49'),(5,5,5,'customer','staff','do you offer airport shuttle?','2024-05-26 11:59:49'),(6,1,1,'customer','manager','can i have an extra pillow?','2024-05-26 11:59:49'),(7,2,2,'customer','manager','can i check in early?','2024-05-26 11:59:49'),(8,3,3,'customer','manager','can i get a late checkout?','2024-05-26 11:59:49'),(9,4,4,'customer','manager','is breakfast included?','2024-05-26 11:59:49'),(10,5,5,'customer','manager','do you offer airport shuttle?','2024-05-26 11:59:49');
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `news`
--

DROP TABLE IF EXISTS `news`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `news` (
  `newsid` int NOT NULL AUTO_INCREMENT,
  `managerid` int DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `content` text,
  `publishedat` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`newsid`),
  KEY `managerid` (`managerid`),
  CONSTRAINT `news_ibfk_1` FOREIGN KEY (`managerid`) REFERENCES `managers` (`managerid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `news`
--

LOCK TABLES `news` WRITE;
/*!40000 ALTER TABLE `news` DISABLE KEYS */;
INSERT INTO `news` VALUES (1,1,'new promotion','check out our latest promotion on drinks!','2024-05-26 11:59:49'),(2,2,'upcoming event','join us for a special event next week.','2024-05-26 11:59:49'),(3,3,'service update','we have improved our booking system.','2024-05-26 11:59:49'),(4,4,'holiday closure','please note that we will be closed for the holidays.','2024-05-26 11:59:49'),(5,5,'customer appreciation','thank you to all our loyal customers for your support.','2024-05-26 11:59:49');
/*!40000 ALTER TABLE `news` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orderhistory`
--

DROP TABLE IF EXISTS `orderhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orderhistory` (
  `orderid` int NOT NULL AUTO_INCREMENT,
  `customerid` int DEFAULT NULL,
  `orderdate` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `totalprice` decimal(10,2) NOT NULL,
  `status` enum('pending','completed','cancelled') DEFAULT NULL,
  `completiondate` timestamp NULL DEFAULT NULL,
  `cancellationdate` timestamp NULL DEFAULT NULL,
  `feedback` text,
  PRIMARY KEY (`orderid`),
  KEY `customerid` (`customerid`),
  CONSTRAINT `orderhistory_ibfk_1` FOREIGN KEY (`orderid`) REFERENCES `orders` (`orderid`),
  CONSTRAINT `orderhistory_ibfk_2` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orderhistory`
--

LOCK TABLES `orderhistory` WRITE;
/*!40000 ALTER TABLE `orderhistory` DISABLE KEYS */;
INSERT INTO `orderhistory` VALUES (1,1,'2024-05-26 11:59:49',15.00,'completed','2024-05-26 11:59:49',NULL,'Great service!'),(2,2,'2024-05-26 11:59:49',30.00,'pending',NULL,NULL,NULL),(3,3,'2024-05-26 11:59:49',45.00,'completed','2024-05-26 11:59:49',NULL,'Loved the product!'),(4,4,'2024-05-26 11:59:49',20.00,'cancelled',NULL,'2024-05-26 11:59:49','Had to cancel due to personal reasons.'),(5,5,'2024-05-26 11:59:49',25.00,'pending',NULL,NULL,NULL);
/*!40000 ALTER TABLE `orderhistory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orderitems`
--

DROP TABLE IF EXISTS `orderitems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orderitems` (
  `orderitemid` int NOT NULL AUTO_INCREMENT,
  `orderid` int DEFAULT NULL,
  `productid` int DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `specialrequests` text,
  PRIMARY KEY (`orderitemid`),
  KEY `orderid` (`orderid`),
  KEY `productid` (`productid`),
  CONSTRAINT `orderitems_ibfk_1` FOREIGN KEY (`orderid`) REFERENCES `orders` (`orderid`),
  CONSTRAINT `orderitems_ibfk_2` FOREIGN KEY (`productid`) REFERENCES `products` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=93 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orderitems`
--

LOCK TABLES `orderitems` WRITE;
/*!40000 ALTER TABLE `orderitems` DISABLE KEYS */;
INSERT INTO `orderitems` (orderid, productid, quantity, specialrequests) VALUES
(88, 1, 2, 'extra hot'),
(88, 2, 3, 'no sugar'),
(89, 3, 1, 'add logo'),
(89, 4, 1, 'extra pillows'),
(90, 5, 2, 'include breakfast'),
(91, 6, 1, ''),
(91, 7, 1, 'Toppings: whipped_cream; Milk: almond; Spice: mild'),
(92, 8, 1, 'Toppings: caramel; Milk: almond; Spice: mild'),
(92, 9, 1, ''),
(93, 10, 1, ''),
(93, 11, 1, ''),
(94, 12, 1, ''),
(94, 13, 1, ''),
(95, 14, 1, ''),
(95, 15, 1, ''),
(96, 16, 1, ''),
(96, 17, 1, ''),
(97, 1, 1, ''),
(97, 2, 1, ''),
(98, 3, 1, 'no sugar'),
(99, 5, 2, 'include breakfast'),
(99, 6, 1, ''),
(100, 7, 1, 'Toppings: whipped_cream; Milk: almond; Spice: mild'),
(100, 8, 1, 'Toppings: caramel; Milk: almond; Spice: mild'),
(101, 9, 1, ''),
(101, 10, 1, ''),
(102, 11, 1, ''),
(102, 12, 1, ''),
(103, 13, 1, ''),
(103, 14, 1, ''),
(104, 15, 1, ''),
(104, 16, 1, ''),
(105, 17, 1, '');/*!40000 ALTER TABLE `orderitems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `orderid` int NOT NULL AUTO_INCREMENT,
  `customerid` int DEFAULT NULL,
  `staffid` int DEFAULT NULL,
  `orderdate` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `totalprice` decimal(10,2) NOT NULL,
  `status` enum('pending','confirmed','preparing','ready','completed','cancelled') DEFAULT NULL,
  `ordertype` enum('now','later') NOT NULL,
  `scheduledate` date DEFAULT NULL,
  `scheduletime` time DEFAULT NULL,
  `estimated_time` int DEFAULT '0',
  PRIMARY KEY (`orderid`),
  KEY `customerid` (`customerid`),
  KEY `staffid` (`staffid`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`),
  CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`staffid`) REFERENCES `staff` (`staffid`)
) ENGINE=InnoDB AUTO_INCREMENT=88 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` (orderid, customerid, staffid, orderdate, totalprice, status, ordertype, scheduledate, scheduletime, estimated_time) VALUES
(88, 1, NULL, '2024-06-01 10:00:00', 20.00, 'completed', 'now', NULL, NULL, 10),
(89, 2, NULL, '2024-06-02 11:00:00', 15.00, 'completed', 'now', NULL, NULL, 8),
(90, 3, NULL, '2024-06-03 12:00:00', 25.00, 'completed', 'now', NULL, NULL, 12),
(91, 4, NULL, '2024-06-04 13:00:00', 30.00, 'completed', 'now', NULL, NULL, 15),
(92, 5, NULL, '2024-06-05 14:00:00', 18.00, 'completed', 'now', NULL, NULL, 9),
(93, 1, NULL, '2024-06-06 15:00:00', 22.00, 'completed', 'now', NULL, NULL, 11),
(94, 2, NULL, '2024-06-07 16:00:00', 16.00, 'completed', 'now', NULL, NULL, 8),
(95, 3, NULL, '2024-06-08 17:00:00', 28.00, 'completed', 'now', NULL, NULL, 14),
(96, 4, NULL, '2024-06-09 18:00:00', 32.00, 'completed', 'now', NULL, NULL, 16),
(97, 5, NULL, '2024-06-10 19:00:00', 19.00, 'completed', 'now', NULL, NULL, 10),
(99, 2, NULL, '2024-06-12 21:00:00', 17.00, 'completed', 'now', NULL, NULL, 8),
(100, 3, NULL, '2024-06-13 22:00:00', 29.00, 'completed', 'now', NULL, NULL, 15),
(101, 4, NULL, '2024-06-14 23:00:00', 33.00, 'completed', 'now', NULL, NULL, 16),
(102, 5, NULL, '2024-06-15 09:00:00', 20.00, 'completed', 'now', NULL, NULL, 10);/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

-- Ensure tables are not locked initially
UNLOCK TABLES;

-- Table structure for table `orderstatuses`
--

DROP TABLE IF EXISTS `orderstatuses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orderstatuses` (
  `statusid` int NOT NULL AUTO_INCREMENT,
  `orderid` int DEFAULT NULL,
  `status` enum('received','waiting','ready','finished') DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`statusid`),
  KEY `orderid` (`orderid`),
  CONSTRAINT `orderstatuses_ibfk_1` FOREIGN KEY (`orderid`) REFERENCES `orders` (`orderid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orderstatuses`
--

LOCK TABLES `orderstatuses` WRITE;
/*!40000 ALTER TABLE `orderstatuses` DISABLE KEYS */;
INSERT INTO `orderstatuses` VALUES (1,1,'received','2024-05-26 11:59:49'),(2,2,'waiting','2024-05-26 11:59:49'),(3,3,'received','2024-05-26 11:59:49'),(4,4,'finished','2024-05-26 11:59:49'),(5,5,'waiting','2024-05-26 11:59:49');
/*!40000 ALTER TABLE `orderstatuses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `paymentinfo`
--

DROP TABLE IF EXISTS `paymentinfo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paymentinfo` (
  `paymentinfoid` int NOT NULL AUTO_INCREMENT,
  `customerid` int DEFAULT NULL,
  `cardtype` varchar(50) DEFAULT NULL,
  `cardnumber` varchar(255) DEFAULT NULL,
  `expiry` date DEFAULT NULL,
  `cvv` varchar(10) DEFAULT NULL,
  `billingaddress` text,
  PRIMARY KEY (`paymentinfoid`),
  KEY `customerid` (`customerid`),
  CONSTRAINT `paymentinfo_ibfk_1` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paymentinfo`
--

LOCK TABLES `paymentinfo` WRITE;
/*!40000 ALTER TABLE `paymentinfo` DISABLE KEYS */;
INSERT INTO `paymentinfo` VALUES (1,1,'visa','4111111111111111','2025-12-31','123','123 maple street'),(2,2,'mastercard','5500000000000004','2026-07-31','456','456 oak street'),(3,3,'amex','340000000000009','2027-05-31','789','789 pine street'),(4,4,'visa','4111111111111112','2025-11-30','101','101 elm street'),(5,5,'mastercard','5500000000000005','2026-06-30','202','202 cedar street');
/*!40000 ALTER TABLE `paymentinfo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `productid` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text,
  `category` enum('food','drink','merchandise','accommodation') DEFAULT NULL,
  `price` decimal(10,2) NOT NULL,
  `image` varchar(255) DEFAULT NULL,
  `isavailable` tinyint(1) DEFAULT '1',
  `default_prep_time` int DEFAULT '5',
  PRIMARY KEY (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES 
(1, 'Americano', 'A strong espresso drink', 'drink', 3.00, 'americano.jpg', 1, 10),
(2, 'Blueberry Muffin', 'Fresh muffin with blueberries', 'food', 2.50, 'blueberry_muffin.jpg', 1, 10),
(3, 'Bruce Bay Cap', 'Stylish cap with logo', 'merchandise', 15.00, 'bruce_bay_cap.jpg', 1, 10),
(4, 'Coffee', 'Full range of coffees with special milks and syrups', 'drink', 3.00, 'coffee.jpg', 1, 10),
(5, 'Soft Drink', 'Various soft drinks', 'drink', 2.00, 'soft_drink.jpg', 1, 10),
(6, 'Milkshake', 'Various milkshake flavors', 'drink', 4.50, 'milkshake.jpg', 1, 10),
(7, 'Iced Tea', 'Various iced tea flavors', 'drink', 3.50, 'iced_tea.jpg', 1, 10),
(8, 'American Hotdog', 'American style hotdogs', 'food', 5.00, 'hotdog.jpg', 1, 10),
(9, 'Sweetcorn & Kumara Patties', 'Sweetcorn and kumara patties', 'food', 6.00, 'patties.jpg', 1, 10),
(10, 'Crepes', 'Crepes with various toppings', 'food', 7.00, 'crepes.jpg', 1, 10),
(11, 'Smokey BBQ Pulled Pork in a Bun', 'Pulled pork with BBQ sauce in a bun', 'food', 8.00, 'pulled_pork.jpg', 1, 10),
(12, 'Muffin', 'Assorted muffins', 'food', 3.00, 'muffin.jpg', 1, 10),
(13, 'Slice', 'Assorted slices', 'food', 2.50, 'slice.jpg', 1, 10),
(14, 'Ice Block', 'Assorted ice blocks', 'food', 1.50, 'ice_block.jpg', 1, 10),
(15, 'Real Fruit Ice Cream', 'Ice cream made with real fruit', 'food', 4.00, 'fruit_ice_cream.jpg', 1, 10),
(16, 'Dorm Room', 'A shared room with 4 single beds', 'accommodation', 30.00, 'dorm_room1.png', 1, 0),
(17, 'Queen Room', 'A room with a queen bed and pull-out sofa', 'accommodation', 100.00, 'queen_room.jpg', 1, 0),
(18, 'Twin Room', 'A room with two single beds', 'accommodation', 45.00, 'twin_room.jpg', 1, 0);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `promotions`
--

DROP TABLE IF EXISTS `promotions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `promotions` (
  `promotionid` int NOT NULL AUTO_INCREMENT,
  `code` varchar(255) DEFAULT NULL,
  `description` text,
  `discountpercent` decimal(5,2) DEFAULT NULL,
  `validfrom` date DEFAULT NULL,
  `validto` date DEFAULT NULL,
  `productid` int DEFAULT NULL,
  PRIMARY KEY (`promotionid`),
  UNIQUE KEY `code` (`code`),
  KEY `productid` (`productid`),
  CONSTRAINT `promotions_ibfk_1` FOREIGN KEY (`productid`) REFERENCES `products` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `promotions`
--

LOCK TABLES `promotions` WRITE;
/*!40000 ALTER TABLE `promotions` DISABLE KEYS */;
INSERT INTO `promotions` VALUES (1,'summer20','20% off on drinks during summer',20.00,'2024-06-01','2024-08-31',1),(2,'winter10','10% off during winter',10.00,'2024-12-01','2025-02-28',2),(3,'spring5','5% off storewide during spring',5.00,'2024-03-01','2024-05-31',3),(4,'fall10','10% off on merchandise during fall',10.00,'2024-09-01','2024-11-30',4),(5,'newyear15','15% off on new year\'s day',15.00,'2025-01-01','2025-01-01',5);
/*!40000 ALTER TABLE `promotions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reviews`
--

DROP TABLE IF EXISTS `reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reviews` (
  `reviewid` int NOT NULL AUTO_INCREMENT,
  `customerid` int DEFAULT NULL,
  `productid` int DEFAULT NULL,
  `rating` int DEFAULT NULL,
  `comment` text,
  `reviewdate` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reviewid`),
  KEY `customerid` (`customerid`),
  KEY `productid` (`productid`),
  CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`),
  CONSTRAINT `reviews_ibfk_2` FOREIGN KEY (`productid`) REFERENCES `products` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reviews`
--

LOCK TABLES `reviews` WRITE;
/*!40000 ALTER TABLE `reviews` DISABLE KEYS */;
INSERT INTO `reviews` VALUES (1,1,1,5,'best coffee ever!','2024-05-26 11:59:49'),(2,2,2,4,'delicious muffin, a bit sweet though.','2024-05-26 11:59:49'),(3,3,3,3,'nice cap, but could be cheaper.','2024-05-26 11:59:49'),(4,4,4,4,'comfortable room, good service.','2024-05-26 11:59:49'),(5,5,5,5,'perfect stay, loved the privacy.','2024-05-26 11:59:49');
/*!40000 ALTER TABLE `reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `scheduleorders`
--

DROP TABLE IF EXISTS `scheduleorders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scheduleorders` (
  `scheduleorderid` int NOT NULL AUTO_INCREMENT,
  `customerid` int DEFAULT NULL,
  `productid` int DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `scheduledate` date DEFAULT NULL,
  `scheduletime` time DEFAULT NULL,
  `status` enum('pending','scheduled','cancelled') DEFAULT NULL,
  PRIMARY KEY (`scheduleorderid`),
  KEY `customerid` (`customerid`),
  KEY `productid` (`productid`),
  CONSTRAINT `scheduleorders_ibfk_1` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`),
  CONSTRAINT `scheduleorders_ibfk_2` FOREIGN KEY (`productid`) REFERENCES `products` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scheduleorders`
--

LOCK TABLES `scheduleorders` WRITE;
/*!40000 ALTER TABLE `scheduleorders` DISABLE KEYS */;
INSERT INTO `scheduleorders` VALUES (1,1,1,2,'2024-07-01','10:00:00','scheduled'),(2,2,2,3,'2024-07-03','11:00:00','pending'),(3,3,3,1,'2024-07-05','12:00:00','scheduled'),(4,4,4,1,'2024-07-07','13:00:00','cancelled'),(5,5,5,2,'2024-07-09','14:00:00','pending'),(6,1,2,1,'2024-05-31','17:12:00','scheduled'),(7,1,2,1,'2024-06-06','21:57:00','scheduled'),(8,1,2,1,'2024-06-06','11:54:00','scheduled'),(9,1,1,1,'2024-06-07','12:24:00','scheduled'),(10,1,1,1,'2024-06-07','12:24:00','scheduled'),(11,1,1,1,'2024-06-07','12:24:00','scheduled'),(12,1,1,1,'2024-06-07','12:24:00','scheduled'),(13,1,1,1,'2024-06-07','12:24:00','scheduled'),(14,1,1,1,'2024-06-07','12:24:00','scheduled'),(15,1,2,1,'2024-06-06','12:24:00','scheduled'),(16,1,2,1,'2024-06-06','12:24:00','scheduled'),(17,1,2,1,'2024-06-06','12:24:00','scheduled'),(18,1,2,1,'2024-06-06','12:24:00','scheduled'),(19,1,2,1,'2024-06-06','12:26:00','scheduled'),(20,1,1,1,'2024-06-07','13:56:00','scheduled'),(21,1,2,1,'2024-06-04','14:32:00','scheduled');
/*!40000 ALTER TABLE `scheduleorders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shoppingcart`
--

DROP TABLE IF EXISTS `shoppingcart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shoppingcart` (
  `shoppingcartid` int NOT NULL AUTO_INCREMENT,
  `customerid` int DEFAULT NULL,
  `productid` int DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `addedat` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`shoppingcartid`),
  KEY `customerid` (`customerid`),
  KEY `productid` (`productid`),
  CONSTRAINT `shoppingcart_ibfk_1` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`),
  CONSTRAINT `shoppingcart_ibfk_2` FOREIGN KEY (`productid`) REFERENCES `products` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shoppingcart`
--

LOCK TABLES `shoppingcart` WRITE;
/*!40000 ALTER TABLE `shoppingcart` DISABLE KEYS */;
INSERT INTO `shoppingcart` VALUES (1,1,1,2,'2024-05-26 11:59:49'),(2,2,2,3,'2024-05-26 11:59:49'),(3,3,3,1,'2024-05-26 11:59:49'),(4,4,4,1,'2024-05-26 11:59:49'),(5,5,5,2,'2024-05-26 11:59:49');
/*!40000 ALTER TABLE `shoppingcart` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff`
--

DROP TABLE IF EXISTS `staff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff` (
  `staffid` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `passwordhash` varchar(255) NOT NULL,
  `createdat` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `lastlogin` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`staffid`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff`
--

LOCK TABLES `staff` WRITE;
/*!40000 ALTER TABLE `staff` DISABLE KEYS */;
INSERT INTO `staff` VALUES (1,'franksinatra','frank.sinatra@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL),(2,'gracekelly','grace.kelly@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL),(3,'hankwilliams','hank.williams@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL),(4,'ingridbergman','ingrid.bergman@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL),(5,'jamesdean','james.dean@example.com','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','2024-05-26 11:59:49',NULL);
/*!40000 ALTER TABLE `staff` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usercredentials`
--

DROP TABLE IF EXISTS `usercredentials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usercredentials` (
  `userid` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `passwordhash` varchar(255) NOT NULL,
  `usertype` enum('customer','staff','manager') NOT NULL,
  `customerid` int DEFAULT NULL,
  `staffid` int DEFAULT NULL,
  `managerid` int DEFAULT NULL,
  PRIMARY KEY (`userid`),
  UNIQUE KEY `username` (`username`),
  KEY `customerid` (`customerid`),
  KEY `staffid` (`staffid`),
  KEY `managerid` (`managerid`),
  CONSTRAINT `usercredentials_ibfk_1` FOREIGN KEY (`customerid`) REFERENCES `customers` (`customerid`) ON DELETE CASCADE,
  CONSTRAINT `usercredentials_ibfk_2` FOREIGN KEY (`staffid`) REFERENCES `staff` (`staffid`) ON DELETE CASCADE,
  CONSTRAINT `usercredentials_ibfk_3` FOREIGN KEY (`managerid`) REFERENCES `managers` (`managerid`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usercredentials`
--

LOCK TABLES `usercredentials` WRITE;
/*!40000 ALTER TABLE `usercredentials` DISABLE KEYS */;
INSERT INTO `usercredentials` VALUES (0,'Walk-in Customer','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','customer',0,NULL,NULL),(1,'emmasmith','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','customer',1,NULL,NULL),(2,'liamjones','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','customer',2,NULL,NULL),(3,'oliviabrown','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','customer',3,NULL,NULL),(4,'noahwilson','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','customer',4,NULL,NULL),(5,'avadavis','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','customer',5,NULL,NULL),(6,'franksinatra','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','staff',NULL,1,NULL),(7,'gracekelly','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','staff',NULL,2,NULL),(8,'hankwilliams','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','staff',NULL,3,NULL),(9,'ingridbergman','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','staff',NULL,4,NULL),(10,'jamesdean','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','staff',NULL,5,NULL),(11,'alicecooper','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','manager',NULL,NULL,1),(12,'bobmarley','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','manager',NULL,NULL,2),(13,'charliechaplin','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','manager',NULL,NULL,3),(14,'dianaross','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','manager',NULL,NULL,4),(15,'elvispresley','41e5257d12a2350a009bee0534856b043af81d88bff707884364bfff76c90025','manager',NULL,NULL,5);
/*!40000 ALTER TABLE `usercredentials` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-05-31 23:29:27
-- phpMyAdmin SQL Dump
-- version 3.5.5
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Jan 25, 2013 at 02:21 PM
-- Server version: 5.5.29-log
-- PHP Version: 5.4.11

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `MALMan2`
--

-- --------------------------------------------------------

--
-- Table structure for table `accounting_attachments`
--

CREATE TABLE IF NOT EXISTS `accounting_attachments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` text NOT NULL,
  `transaction_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=21 ;

-- --------------------------------------------------------

--
-- Table structure for table `accounting_attachments_transactions`
--

CREATE TABLE IF NOT EXISTS `accounting_attachments_transactions` (
  `attachment_id` int(11) NOT NULL,
  `transaction_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `accounting_banks`
--

CREATE TABLE IF NOT EXISTS `accounting_banks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=100 ;

--
-- Dumping data for table `accounting_banks`
--

INSERT INTO `accounting_banks` (`id`, `name`) VALUES
(1, 'Argenta'),
(2, 'ING'),
(99, 'cash');

-- --------------------------------------------------------

--
-- Table structure for table `accounting_cashregister`
--

CREATE TABLE IF NOT EXISTS `accounting_cashregister` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `purchase_id` int(11) DEFAULT NULL,
  `amount` decimal(10,2) NOT NULL,
  `description` text NOT NULL,
  `datetime` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=14 ;

-- --------------------------------------------------------

--
-- Table structure for table `accounting_categories`
--

CREATE TABLE IF NOT EXISTS `accounting_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `legal_category` varchar(255) NOT NULL,
  `is_revenue` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=12 ;

--
-- Dumping data for table `accounting_categories`
--

INSERT INTO `accounting_categories` (`id`, `name`, `legal_category`, `is_revenue`) VALUES
(1, 'rent', 'Diverse Goederen en Diensten', 0),
(2, 'purchase of various supplies', 'Diverse Goederen en Diensten', 0),
(3, 'investments', 'Diverse Goederen en Diensten', 0),
(4, 'purchases of stock for the bar', 'Goederen en Diensten', 0),
(5, 'sale of food and drinks', 'Verkopen Handelsgoederen', 1),
(6, 'bar account', 'Verkopen Handelsgoederen', 1),
(7, 'cash deposit', 'Transfer', 1),
(8, 'membership dues', 'Bijdragen', 1),
(9, 'workshop partipation', 'Giften', 1),
(10, 'feed the hackers', 'Giften', 1),
(11, 'misc. donation', 'Gift', 1);

-- --------------------------------------------------------

--
-- Table structure for table `accounting_transactions`
--

CREATE TABLE IF NOT EXISTS `accounting_transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` date DEFAULT NULL,
  `amount` decimal(11,2) NOT NULL,
  `description` text NOT NULL,
  `bank_id` tinyint(4) DEFAULT NULL,
  `bank_statement_number` int(11) DEFAULT NULL,
  `to_from` text NOT NULL,
  `category_id` tinyint(4) DEFAULT NULL,
  `advance_date` date DEFAULT NULL,
  `date_filed` date DEFAULT NULL,
  `filed_by_id` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=133 ;

-- --------------------------------------------------------

--
-- Table structure for table `bar_accounts_log`
--

CREATE TABLE IF NOT EXISTS `bar_accounts_log` (
  `id` tinyint(4) NOT NULL AUTO_INCREMENT,
  `user_id` tinyint(4) NOT NULL,
  `purchase_id` int(11) DEFAULT NULL,
  `transaction_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transaction_id` (`transaction_id`),
  UNIQUE KEY `purchase_id` (`purchase_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=22 ;

-- --------------------------------------------------------

--
-- Table structure for table `bar_categories`
--

CREATE TABLE IF NOT EXISTS `bar_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `beschrijving` (`name`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=4 ;

--
-- Dumping data for table `bar_categories`
--

INSERT INTO `bar_categories` (`id`, `name`) VALUES
(1, 'food'),
(2, 'alcoholic drink'),
(3, 'non-alcoholic drink');

-- --------------------------------------------------------

--
-- Table structure for table `bar_items`
--

CREATE TABLE IF NOT EXISTS `bar_items` (
  `id` int(50) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `stock_max` int(50) NOT NULL,
  `price` decimal(5,2) NOT NULL,
  `category_id` int(50) NOT NULL,
  `josto` int(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `Naam` (`name`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=28 ;

-- --------------------------------------------------------

--
-- Table structure for table `bar_log`
--

CREATE TABLE IF NOT EXISTS `bar_log` (
  `id` int(50) NOT NULL AUTO_INCREMENT,
  `item_id` int(50) NOT NULL,
  `amount` int(50) NOT NULL,
  `price` decimal(5,2) NOT NULL,
  `datetime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user_id` int(50) DEFAULT '0',
  `transaction_type` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=307 ;

-- --------------------------------------------------------

--
-- Table structure for table `members_fees`
--

CREATE TABLE IF NOT EXISTS `members_fees` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `transaction_id` int(11) NOT NULL,
  `until` date NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=3 ;

-- --------------------------------------------------------

--
-- Table structure for table `members_roles`
--

CREATE TABLE IF NOT EXISTS `members_roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=5 ;

--
-- Dumping data for table `members_roles`
--

INSERT INTO `members_roles` (`id`, `name`, `description`) VALUES
(1, 'bar', 'stock beheer van de bar'),
(2, 'members', 'ledenbeheer'),
(3, 'membership', 'is an active member of the hackerspace'),
(4, 'finances', 'edit accounting information');

-- --------------------------------------------------------

--
-- Table structure for table `members_roles_users`
--

CREATE TABLE IF NOT EXISTS `members_roles_users` (
  `user_id` int(11) DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  KEY `user_id` (`user_id`),
  KEY `role_id` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `members_users`
--

CREATE TABLE IF NOT EXISTS `members_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `confirmed_at` datetime DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `street` varchar(255) NOT NULL,
  `number` int(11) NOT NULL,
  `bus` varchar(255) NOT NULL,
  `postalcode` int(11) NOT NULL,
  `city` varchar(255) NOT NULL,
  `date_of_birth` date NOT NULL,
  `telephone` varchar(255) NOT NULL,
  `active_member` tinyint(1) NOT NULL,
  `membership_dues` int(10) NOT NULL,
  `member_since` date NOT NULL,
  `show_telephone` tinyint(1) NOT NULL,
  `show_email` tinyint(1) NOT NULL,
  `motivation` text NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=100 ;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `members_roles_users`
--
ALTER TABLE `members_roles_users`
  ADD CONSTRAINT `members_roles_users_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `members_users` (`id`),
  ADD CONSTRAINT `members_roles_users_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `members_roles` (`id`);
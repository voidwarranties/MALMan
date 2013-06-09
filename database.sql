SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;


CREATE TABLE IF NOT EXISTS `accounting_attachments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `extension` text NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `accounting_attachments_transactions` (
  `attachment_id` int(11) NOT NULL,
  `transaction_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `accounting_banks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

INSERT INTO `accounting_banks` (`id`, `name`) VALUES
(2, 'Bank 2'),
(1, 'Bank 1'),
(99, 'cash');

CREATE TABLE IF NOT EXISTS `accounting_cashregister` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `purchase_id` int(11) DEFAULT NULL,
  `is_revenue` tinyint(1) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `description` text NOT NULL,
  `datetime` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `accounting_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `legal_category` varchar(255) NOT NULL,
  `is_revenue` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

INSERT INTO `accounting_categories` (`id`, `name`, `legal_category`, `is_revenue`) VALUES
(1, 'huur / vaste kosten', 'Diverse Goederen en Diensten', 0),
(2, 'Aankopen diverse goederen en diensten', 'Diverse Goederen en Diensten', 0),
(3, 'investeringen', 'Diverse Goederen en Diensten', 0),
(4, 'aankopen verbruiksgoederen', 'Goederen en Diensten', 0),
(5, 'verkoop verbruiksgoederen', 'Verkopen Handelsgoederen', 1),
(6, 'Aanvullen drankrekening', 'Verkopen Handelsgoederen', 1),
(7, 'Transfer', 'Transfer', 1),
(8, 'Lidgelden', 'Bijdragen', 1),
(9, 'Deelname workshops', 'Giften', 1),
(10, 'feed the hackers', 'Giften', 1),
(11, 'Geld donaties', 'Giften', 1),
(12, 'Bankkosten', 'Overige', 0),
(13, 'Transfer', 'Transfer', 0);

CREATE TABLE IF NOT EXISTS `accounting_transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` date DEFAULT NULL,
  `facturation_date` date DEFAULT NULL,
  `advance_date` date DEFAULT NULL,
  `is_revenue` tinyint(1) NOT NULL,
  `amount` decimal(11,2) NOT NULL,
  `description` text NOT NULL,
  `bank_id` tinyint(4) DEFAULT NULL,
  `bank_statement_number` int(11) DEFAULT NULL,
  `to_from` text NOT NULL,
  `category_id` tinyint(4) DEFAULT NULL,
  `date_filed` date DEFAULT NULL,
  `filed_by_id` tinyint(4) DEFAULT NULL,
  `reimbursement_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `bar_accounts_log` (
  `id` tinyint(4) NOT NULL AUTO_INCREMENT,
  `user_id` tinyint(4) NOT NULL,
  `purchase_id` int(11) DEFAULT NULL,
  `transaction_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transaction_id` (`transaction_id`),
  UNIQUE KEY `purchase_id` (`purchase_id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `bar_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `beschrijving` (`name`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1;

INSERT INTO `bar_categories` (`id`, `name`) VALUES
(1, 'food'),
(2, 'alcoholic drink'),
(3, 'non-alcoholic drink');

CREATE TABLE IF NOT EXISTS `bar_items` (
  `id` int(50) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `stock_max` int(50) NOT NULL,
  `price` decimal(5,2) NOT NULL,
  `category_id` int(50) NOT NULL,
  `josto` tinyint(1) NOT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `Naam` (`name`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `bar_log` (
  `id` int(50) NOT NULL AUTO_INCREMENT,
  `item_id` int(50) NOT NULL,
  `amount` int(50) NOT NULL,
  `price` decimal(5,2) NOT NULL,
  `datetime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user_id` int(50) DEFAULT NULL,
  `transaction_type` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `members` (
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
  `membership_dues` decimal(5,2) NOT NULL,
  `member_since` date NOT NULL,
  `show_telephone` tinyint(1) NOT NULL,
  `show_email` tinyint(1) NOT NULL,
  `motivation` text NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `members_fees` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `transaction_id` int(11) NOT NULL,
  `until` date NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `members_roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

INSERT INTO `members_roles` (`id`, `name`, `description`) VALUES
(1, 'bar', 'stock beheer van de bar'),
(2, 'members', 'ledenbeheer'),
(3, 'finances', 'edit accounting information');

CREATE TABLE IF NOT EXISTS `members_roles_users` (
  `user_id` int(11) DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  KEY `user_id` (`user_id`),
  KEY `role_id` (`role_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

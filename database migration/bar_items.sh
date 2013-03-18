#!/bin/bash

if [ $# -eq 0 ]; then
    echo "this program takes one argument: the filepath to an sql dump of the MALMan1 Bar table"
    exit 1
fi

echo '
SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf9 */;

INSERT INTO `bar_items` (`ID`, `Name`, `Barcode`, `Price`, `Josto`, `Type`, `Stock`, `Minimum`) VALUES
'

IFS=','
grep '^(' $1 | while read id name barcode price josto type stock minimum; do
	echo "(${id#(}", "$name", "${minimum%)}", "$price", "$type", "$josto"\),
done | sed "s/'NonAlc'/3/;s/'Alc'/2/;s/'Food'/1/;s/);//;" | sed '$ s/),/);/'
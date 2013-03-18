#!/bin/bash

if [ $# -eq 0 ]; then
    echo "this program takes one argument: the filepath to an sql dump of the MALMan1 Users table"
    exit 1
fi

echo '
SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

INSERT INTO `members` (`id`, `email`, `password`, `active`, `confirmed_at`, `name`, `street`, `number`, `bus`, `postalcode`, `city`, `date_of_birth`, `telephone`, `active_member`, `membership_dues`, `member_since`, `show_telephone`, `show_email`, `motivation`) VALUES
'

IFS=','
grep '^(' $1 | sed 's/,Accounting//;s/,Members//;s/,Library//' | while read id firstname lastname street housenr postcode city email showemail phone showphone dob baraccount password role active; do
	echo "(${id#(}", "$email", "'password'", 1, "'confirmed'", "${firstname%?}" "${lastname#??}", "$street", "$housenr", "'bus'", "$postcode", "$city", "$dob", "$phone", "${active%)}", "0", "'0000-00-00'", "$showphone", "$showemail", "'motivation'"\),

done | sed ";s/);//;" | sed '$ s/),/);/'
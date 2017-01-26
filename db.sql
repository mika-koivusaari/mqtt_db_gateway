CREATE TABLE `data` (
  `sensorid` bigint(20) unsigned NOT NULL,
  `time` datetime NOT NULL,
  `value` decimal(15,5) NOT NULL,
  KEY `sensordata` (`sensorid`,`time`),
  KEY `data_timeid` (`time`,`sensorid`),
  KEY `sensordata2` (`sensorid`,`time`,`value`),
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `datatext` (
  `sensorid` bigint(20) unsigned NOT NULL,
  `time` datetime NOT NULL,
  `text` varchar(2000) NOT NULL,
  KEY `sensordatatext` (`sensorid`,`time`),
  KEY `datatext_timeid` (`time`,`sensorid`),
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `mqtt_input` (
  `topic` varchar(200) NOT NULL,
  `topic_regexp` varchar(1000) DEFAULT NULL,
  `message_regexp` varchar(1000) DEFAULT NULL,
  `process_value` varchar(2000) DEFAULT NULL,
  `process_time` varchar(2000) DEFAULT NULL,
  `process_value_type` int(11) NOT NULL DEFAULT '1' COMMENT '1=expression\n2=format string\n3=exec\n',
  `process_time_type` int(11) NOT NULL DEFAULT '1',
  PRIMARY KEY (`topic`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `rawid_sensorid` (
  `rawid` varchar(100) NOT NULL,
  `sensorid` bigint(20) NOT NULL,
  PRIMARY KEY (`rawid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

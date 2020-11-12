# Mysql setting for ITAF v.0.0.1

CREATE DATABASE IF NOT EXISTS itaf;
use itaf;

DROP TABLE IF EXISTS `wd_opts`;
CREATE TABLE `wd_opts` (`opt` varchar(64));
DROP TABLE IF EXISTS `caps_opts`;
CREATE TABLE `caps_opts` (`opt` varchar(64));
DROP TABLE IF EXISTS `tsrv_inf`;
CREATE TABLE `tsrv_inf` (
	`sname` varchar(32),
	`ip` varchar(15),
	`port` int,
	`userid` varchar(32),
	`passwd` varchar(32)
	);
DROP TABLE IF EXISTS `encdir`; 
CREATE TABLE `encdir` (
	`ip` varchar(15),
	`path` varchar(4096),
	`enctype` int
);
DROP TABLE IF EXISTS `mgr_inf`;
CREATE TABLE `mgr_inf` (
	`name` varchar(32),
	`value` varchar(128)
);

DROP TABLE IF EXISTS `acc_obj`;
CREATE TABLE `acc_obj`(`name` varchar(255));
DROP TABLE IF EXISTS `ip_obj`;
CREATE TABLE `ip_obj`(`name` varchar(255));
DROP TABLE IF EXISTS `proc_obj`;
CREATE TABLE `proc_obj`(`name` varchar(255));
DROP TABLE IF EXISTS `path_obj`;
CREATE TABLE `path_obj`(`name` varchar(255));

DROP TABLE IF EXISTS `dec_pol`;
CREATE TABLE `dec_pol`(
	`idx`	int,
	`action` int,
	`account` varchar(255),
	`ip` varchar(15),
	`proc` varchar(255),
	`path` varchar(4096)
);
-- Action
-- 11 : Allow decrypt and Logging
-- 10 : Allow decrypt, Not Logging
-- 00 : Deny decrypt, Deny Read
-- 01: Deny decrypt, Allow Read

DROP TABLE IF EXISTS `acl_pol`;
CREATE TABLE `acl_pol` (
	`idx`	int,
	`account` varchar(255),
	`ip` varchar(15),
	`proc` varchar(255),
	`path` varchar(4096)
);

DROP TABLE IF EXISTS `pol_order`;
CREATE TABLE `pol_order` (
	`sname` varchar(32),
	`pol_idx` int,
	`pol_type` boolean
);

DROP TABLE IF EXISTS `vm_inf`;
CREATE TABLE `vm_inf` (
	`ip` varchar(15),
	`type` varchar(32),
	`id` varchar(32),
	`pw` varchar(32)
);

INSERT INTO `mgr_inf` VALUES("vip", "192.168.106.113");
INSERT INTO `mgr_inf` VALUES("rip1", "192.168.106.114");
INSERT INTO `mgr_inf` VALUES("rip2", "192.168.106.115");
INSERT INTO `mgr_inf` VALUES("webport", "3443");
INSERT INTO `mgr_inf` VALUES("sshport", "22");
INSERT INTO `mgr_inf` VALUES("sshid", "root");
INSERT INTO `mgr_inf` VALUES("sshpw", "dbsafer00");
INSERT INTO `mgr_inf` VALUES("dcmgrid","admin");
INSERT INTO `mgr_inf` VALUES("dcmgrpw","admin007");
INSERT INTO `mgr_inf` VALUES("kmsid","admin");
INSERT INTO `mgr_inf` VALUES("kmspw","admin007");
INSERT INTO `mgr_inf` VALUES("mysqlid","root");
INSERT INTO `mgr_inf` VALUES("mysqlpw","dbsafer00");
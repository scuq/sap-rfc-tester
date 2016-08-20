#!/usr/bin/env /usr/bin/python
# -*- coding: utf-8 -*-
me = "sap-rfc-tester"
import sys
import json
import os
import sapnwrfc
from optparse import OptionParser
import time
import logging
import codecs
try:
	import rrdtool
except:
	logger.error("error while importing rrdtool module")

if not sys.platform == "win32":
	from logging.handlers import SysLogHandler

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)s '+me+' %(message)s')


if sys.platform == 'win32':
	hdlr = logging.FileHandler(os.path.normpath(os.environ["USERPROFILE"]+os.sep+__name__+".log"))
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr) 

else:
	syslog = SysLogHandler(address='/dev/log',facility="local5")
	syslog.setFormatter(formatter)
	logger.addHandler(syslog)

logger.setLevel(logging.INFO)




dirs={1: 'IMPORT', 2: 'EXPORT', 3: 'CHANGING', 7: 'TABLES'} # See sapnwrfc.IMPORT, ...

sap_types={
    0: 'CHAR',
    1: 'DATE',
    2: 'BCD',
    3: 'TIME',
    4: 'BYTE',
    5: 'TABLE',
    6: 'NUM',
    7: 'FLOAT',
    8: 'INT',
    9: 'INT2',
    10: 'INT1',
    14: 'NULL',
    17: 'STRUCTURE',
    23: 'DECF16',
    24: 'DECF34',
    28: 'XMLDATA',
    29: 'STRING',
    30: 'XSTRING',
    98: 'EXCEPTION',
    }

def print_rfc_interface(method_name, conn=None):
	if conn is None:
		conn = sapnwrfc.base.rfc_connect(cfg=SAP_CONNECTION)
	iface = conn.discover(method_name)
	print(iface.name)
	for key, var_dict in sorted(iface.handle.parameters.items()):
		#Example: {'direction': 1, 'name': 'ARCHIV_DOC_ID', 'type': 0, 'len': 40, 'decimals': 0, 'ulen': 80}
		value=dict(var_dict)
		name=value.pop('name')
		assert key==name, (key, name)
		direction=value.pop('direction')
		direction=dirs.get(direction, direction)
		sap_type=value.pop('type')
		sap_type=sap_types.get(sap_type, sap_type)
		print(key, 'direction=%s type=%s len=%s decimals=%s ulen=%s rest=%s' % (direction, sap_type, value.pop('len'), value.pop('decimals'), value.pop('ulen'), value))


def sap_connect(logger,ts_start,ts_last):

	conn = None
	
	try:
		conn = sapnwrfc.base.rfc_connect()
		ela_log(logger,ts_start,ts_last,"sap-rfc connection established")
		ts_last=time.time()
		ela_log(logger,ts_start,ts_last,"sap-rfc connection attributes:" + str(conn.connection_attributes()))
	except sapnwrfc.RFCCommunicationError:
		ela_log(logger,ts_start,ts_last,"error while connecting via sap-rfc: "+str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]))
		ts_last=time.time()
	    	sys.exit(1)

	return conn, ts_last

def sap_disconnect(logger,ts_start,ts_last,conn):


	
        try:
                conn.close()
                ela_log(logger,ts_start,ts_last,"sap-rfc connection closed")
                ts_last=time.time()
        except sapnwrfc.RFCCommunicationError:
                ela_log(logger,ts_start,ts_last,"error while closing sap-rfc connection: "+str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]))
                ts_last=time.time()
                sys.exit(1)

        return ts_last


def ela_log(logger,ts_start,ts_last,message):

	_ts_elapsed_ss = str('{:.5f}'.format(time.time()-ts_start))
	_ts_elapsed_sl = str('{:.5f}'.format(time.time()-ts_last))
	_ts_elapsed_ss = "tes:"+_ts_elapsed_ss+" "
	_ts_elapsed_sl = "tel:"+_ts_elapsed_sl+"; " 
        logger.info(_ts_elapsed_ss + _ts_elapsed_sl + message)
	return

def dump(obj):
  print "--dump--"
  for attr in dir(obj):
    print "obj.%s = %s" % (attr, getattr(obj, attr))
  print "--enddump--"

def execrfc(rfc_module_name,sap_module_args,sap_conn_config_file,discover_rfc,write_to_stats_log,stats_log_file,write_to_rrd_db,stats_rrd_file):


	ts_start=time.time()
	ts_last=ts_start

		

	ela_log(logger,ts_start,ts_last,"main started, using module: "+rfc_module_name)

	sapnwrfc.base.config_location = sap_conn_config_file
	sapnwrfc.base.load_config()


	ela_log(logger,ts_start,ts_last,"config loaded")
	ts_last=time.time()

	conn, ts_last = sap_connect(logger,ts_start,ts_last)


	if discover_rfc:
		print_rfc_interface(rfc_module_name, conn)
		ela_log(logger,ts_start,ts_last,"rfc interface discovered")
		ts_last=time.time()
	else:


		try:
			rfc_interf = conn.discover(rfc_module_name)
			ela_log(logger,ts_start,ts_last,"rfc interface discovered")
			ts_last=time.time()

			rfc_obj = rfc_interf.create_function_call()
			
			for argname in sap_module_args.keys():
				getattr(rfc_obj, argname)(str(sap_module_args[argname]))

			ela_log(logger,ts_start,ts_last,"rfc sap module parameters set")
			ts_last=time.time()

			ela_log(logger,ts_start,ts_last,"invoking sap module")
			ts_last=time.time()

			rfc_obj.invoke()

			d = rfc_obj.handle.parameters


			ela_log(logger,ts_start,ts_last,"result "+str(sys.getsizeof(d))+"bytes returned")
			ts_last=time.time()

			if write_to_stats_log:
				_ts_elapsed_start_result = str('{:.5f}'.format(time.time()-ts_start))

		except:
			ela_log(logger,ts_start,ts_last,"error while invoking sap module: "+str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]))
			ts_last=time.time()
			ts_last = sap_disconnect(logger,ts_start,ts_last,conn)
	    		sys.exit(1)
			

	ts_last = sap_disconnect(logger,ts_start,ts_last,conn)

	if write_to_stats_log:
		file = codecs.open(stats_log_file, "a", "utf-8")
		file.write(time.strftime("%Y-%d-%m %H:%M:%S", time.localtime())+";"+_ts_elapsed_start_result+"\n")
		file.close()

		if write_to_rrd_db:
			if not os.path.isfile(stats_rrd_file):
				rrdtool.create(stats_rrd_file,
                                                                        '--step', '2s',
                                                                        '--start', 'now-1h',
                                                                        'DS:runtime:GAUGE:20s:-10:60',
                                                                        'RRA:MIN:0.5:1:43200',
                                                                        'RRA:MAX:0.5:1:43200',
                                                                        'RRA:AVERAGE:0.5:1:43200',
                                                                         )
			rrdtool.update(stats_rrd_file, 'N:'+_ts_elapsed_start_result)
			rrdtool.graph(stats_rrd_file.replace(".rrd",".png"),
                                                                        '--imgformat', 'PNG',
                                                                        '--width', '1121',
                                                                        '--height', '313',
                                                                        '--start', "now-1d",
                                                                        '--end', "-1",
                                                                        '--vertical-label', 'runtime',
                                                                        '--title', 'Runtime Module '+rfc_module_name,
                                                                        '--lower-limit', '-10',
                                                                        '--upper-limit', '50',
                                                                        'DEF:runtime='+stats_rrd_file+':runtime:AVERAGE',
                                                                        'LINE:runtime#007F0E:seconds',
                                                                        'HRULE:5#FF6A00',
                                                                        'HRULE:20#FF0000',
                                                                        'GPRINT:runtime:LAST:Current\:%8.5lf',
                                                                        'GPRINT:runtime:AVERAGE:Average\:%8.5lf',
                                                                        'GPRINT:runtime:MAX:Maximum\:%8.5lf'
                                                                        )



def main():


	parser = OptionParser()
	parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="enable verbose output")
	parser.add_option("-d", "--discover-rfc", action="store_true", dest="discoverrfc", default=False, help="discover and print rfc module")
	parser.add_option("-r", "--rfcmodule", dest="rfcmodule", help="name of the sap remote function call module")
	parser.add_option("-l", "--execute-loop", dest="executeloop", help="execute in an infinite loop with specified interval in seconds")
	parser.add_option("-c", "--sapconconf", dest="sapconconf", help="config file path to sap connection config default ./sap.yml")
	parser.add_option("-w", "--stats-logfile", dest="statslogfile", help="write to specified statistics logfile")
	parser.add_option("", "--rrd", action="store_true", dest="statsrrd", default=False, help="write statistics to rrd database needs -w")
	parser.add_option("-i", "--moduleargs", dest="moduleargs", help="sap module args (json format)")


	(options, args) = parser.parse_args()

	rfc_module_name = ""
	sap_conn_config_file = "sap.yml"
	discover_rfc = False
	write_to_stats_log = False
	stats_log_file = "/dev/null"
	write_to_rrd_db = False
	stats_rrd_file = "/dev/null"
	exec_loop = False
	loop_interval = 2

		


	sap_module_args = ""

	if options.moduleargs:
		try:
			sap_module_args = json.loads(options.moduleargs)

		except:
			logger.error("sap module argument parsing (-i) failed")
			pass

	if options.executeloop:
		exec_loop = True
		try:
			loop_interval = int(options.executeloop)
		except:
			pass

	if options.statslogfile:
		write_to_stats_log = True
		stats_log_file = options.statslogfile

		if options.statsrrd:

			write_to_rrd_db = True
			if stats_log_file.count(".") > 0:
				stats_rrd_file = stats_log_file.replace(stats_log_file.split(".")[-1],".rrd")
			else:
				stats_rrd_file = stats_log_file+".rrd"


	if options.sapconconf and os.path.isfile(options.sapconconf):
		sap_conn_config_file = options.sapconconf

	logger.info("loading config from file: "+sap_conn_config_file)
	
	if not options.rfcmodule:
		print "please specify a rfc module name."
		sys.exit(1)
	else:
		rfc_module_name = options.rfcmodule


	if options.discoverrfc:
		discover_rfc = True


	if not exec_loop:
		execrfc(rfc_module_name,sap_module_args,sap_conn_config_file,discover_rfc,write_to_stats_log,stats_log_file,write_to_rrd_db,stats_rrd_file)
	else:
		logger.info("starting infinite loop with an interval of "+str(loop_interval)+" seconds.")
		while True:
			execrfc(rfc_module_name,sap_module_args,sap_conn_config_file,discover_rfc,write_to_stats_log,stats_log_file,write_to_rrd_db,stats_rrd_file)

			time.sleep(loop_interval)



if __name__=='__main__': main()

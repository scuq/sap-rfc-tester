# sap-rfc-tester
SAP RFC Performance Tester (using piersharding/python-sapnwrfc)

Example (Loop):

```
sap-rfc-tester.py -r Z_CUSTOM_SAP_MODULE -i '{  "I_PARM1": "0001", "I_PARAM2": "00002" }' -w /tmp/test --rrd -l 2
```

Example:

```
sap-rfc-tester.py -r Z_CUSTOM_SAP_MODULE -i '{  "I_PARM1": "0001", "I_PARAM2": "00002" }' -w /tmp/test --rrd
```


""" Test API returns no tracking data, use this data for development instead. """
import json

def get_mock_tracking(awb_number):
    data = json.loads(mock_awaiting_pickup)
    data['shipments'][0]['shipmentTrackingNumber'] = awb_number
    return data

mock_awaiting_pickup = """
{
	"shipments": [
		{
			"shipmentTrackingNumber": "1727636691",
			"status": "Success",
			"shipmentTimestamp": "2024-04-19T10:06:31",
			"productCode": "P",
			"description": "Water measurement equipment",
			"shipperDetails": {
				"name": "Unnamed",
				"postalAddress": {
					"cityName": "LEEDS",
					"postalCode": "SDA 124",
					"countryCode": "GB"
				},
				"serviceArea": [
					{
						"code": "BHX",
						"description": "Birmingham-GB"
					}
				]
			},
			"receiverDetails": {
				"name": "ANONYMOUS",
				"postalAddress": {
					"cityName": "ZURICH",
					"postalCode": "8000",
					"countryCode": "CH"
				},
				"serviceArea": [
					{
						"code": "ZRH",
						"description": "Zurich-CH",
						"facilityCode": "ZRH"
					}
				]
			},
			"totalWeight": 5,
			"unitOfMeasurements": "metric",
			"shipperReferences": [
				{
					"value": "DN-01722 RETURN",
					"typeCode": "CU"
				}
			],
			"events": [],
			"numberOfPieces": 1
		}
	]
}
"""

mock_minimal = """
{
	"shipments": [
		{
			"shipmentTrackingNumber": "1727636691",
			"status": "Success",
			"shipmentTimestamp": "2024-04-19T10:06:31",
			"productCode": "P",
			"description": "Water measurement equipment",
			"shipperDetails": {
				"name": "Unnamed",
				"postalAddress": {
					"cityName": "LEEDS",
					"postalCode": "SDA 124",
					"countryCode": "GB"
				},
				"serviceArea": [
					{
						"code": "BHX",
						"description": "Birmingham-GB"
					}
				]
			},
			"receiverDetails": {
				"name": "ANONYMOUS",
				"postalAddress": {
					"cityName": "ZURICH",
					"postalCode": "8000",
					"countryCode": "CH"
				},
				"serviceArea": [
					{
						"code": "ZRH",
						"description": "Zurich-CH",
						"facilityCode": "ZRH"
					}
				]
			},
			"totalWeight": 5,
			"unitOfMeasurements": "metric",
			"shipperReferences": [
				{
					"value": "DN-01722 RETURN",
					"typeCode": "CU"
				}
			],
			"events": [
				{
					"date": "2024-04-27",
					"time": "12:20:03",
					"typeCode": "PU",
					"description": "Shipment picked up",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-27",
					"time": "20:19:30",
					"typeCode": "PL",
					"description": "Processed at GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-27",
					"time": "20:19:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "01:07:08",
					"typeCode": "AF",
					"description": "Arrived at DHL Sort Facility  ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				}
			],
			"numberOfPieces": 1
		}
	]
}
"""

mock_partial = """
{
	"shipments": [
		{
			"shipmentTrackingNumber": "1727636691",
			"status": "Success",
			"shipmentTimestamp": "2024-04-19T10:06:31",
			"productCode": "P",
			"description": "Water measurement equipment",
			"shipperDetails": {
				"name": "Unnamed",
				"postalAddress": {
					"cityName": "LEEDS",
					"postalCode": "SDA 124",
					"countryCode": "GB"
				},
				"serviceArea": [
					{
						"code": "BHX",
						"description": "Birmingham-GB"
					}
				]
			},
			"receiverDetails": {
				"name": "ANONYMOUS",
				"postalAddress": {
					"cityName": "ZURICH",
					"postalCode": "8000",
					"countryCode": "CH"
				},
				"serviceArea": [
					{
						"code": "ZRH",
						"description": "Zurich-CH",
						"facilityCode": "ZRH"
					}
				]
			},
			"totalWeight": 5,
			"unitOfMeasurements": "metric",
			"shipperReferences": [
				{
					"value": "DN-01722 RETURN",
					"typeCode": "CU"
				}
			],
			"events": [
				{
					"date": "2024-04-27",
					"time": "12:20:03",
					"typeCode": "PU",
					"description": "Shipment picked up",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-27",
					"time": "20:19:30",
					"typeCode": "PL",
					"description": "Processed at GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-27",
					"time": "20:19:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "01:07:08",
					"typeCode": "AF",
					"description": "Arrived at DHL Sort Facility  ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "03:44:45",
					"typeCode": "PL",
					"description": "Processed at ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "03:44:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "07:05:00",
					"typeCode": "AR",
					"description": "Arrived at DHL Delivery Facility  GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "09:22:57",
					"typeCode": "MS",
					"description": "Shipment arrived at incorrect facility. It will be sent to the correct destination for delivery",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "20:13:20",
					"typeCode": "PL",
					"description": "Processed at GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "20:13:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-05-02",
					"time": "04:04:48",
					"typeCode": "PL",
					"description": "Processed at ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-05-02",
					"time": "04:04:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-05-02",
					"time": "05:18:37",
					"typeCode": "AR",
					"description": "Arrived at DHL Delivery Facility  ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				}
			],
			"numberOfPieces": 1
		}
	]
}
"""

mock_full = """
{
	"shipments": [
		{
			"shipmentTrackingNumber": "1727636691",
			"status": "Success",
			"shipmentTimestamp": "2024-04-19T10:06:31",
			"productCode": "P",
			"description": "Water measurement equipment",
			"shipperDetails": {
				"name": "Unnamed",
				"postalAddress": {
					"cityName": "LEEDS",
					"postalCode": "SDA 124",
					"countryCode": "GB"
				},
				"serviceArea": [
					{
						"code": "BHX",
						"description": "Birmingham-GB"
					}
				]
			},
			"receiverDetails": {
				"name": "ANONYMOUS",
				"postalAddress": {
					"cityName": "ZURICH",
					"postalCode": "8000",
					"countryCode": "CH"
				},
				"serviceArea": [
					{
						"code": "ZRH",
						"description": "Zurich-CH",
						"facilityCode": "ZRH"
					}
				]
			},
			"totalWeight": 5,
			"unitOfMeasurements": "metric",
			"shipperReferences": [
				{
					"value": "DN-01722 RETURN",
					"typeCode": "CU"
				}
			],
			"events": [
				{
					"date": "2024-04-27",
					"time": "12:20:03",
					"typeCode": "PU",
					"description": "Shipment picked up",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-27",
					"time": "20:19:30",
					"typeCode": "PL",
					"description": "Processed at GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-27",
					"time": "20:19:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "01:07:08",
					"typeCode": "AF",
					"description": "Arrived at DHL Sort Facility  ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "03:44:45",
					"typeCode": "PL",
					"description": "Processed at ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "03:44:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "07:05:00",
					"typeCode": "AR",
					"description": "Arrived at DHL Delivery Facility  GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "09:22:57",
					"typeCode": "MS",
					"description": "Shipment arrived at incorrect facility. It will be sent to the correct destination for delivery",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "20:13:20",
					"typeCode": "PL",
					"description": "Processed at GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-04-29",
					"time": "20:13:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility GENEVA-SWITZERLAND",
					"serviceArea": [
						{
							"code": "GVA",
							"description": "Geneva-CH"
						}
					]
				},
				{
					"date": "2024-05-02",
					"time": "04:04:48",
					"typeCode": "PL",
					"description": "Processed at ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-05-02",
					"time": "04:04:58",
					"typeCode": "DF",
					"description": "Shipment has departed from a DHL facility ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-05-02",
					"time": "05:18:37",
					"typeCode": "AR",
					"description": "Arrived at DHL Delivery Facility  ZURICH-SWITZERLAND",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-05-02",
					"time": "05:37:01",
					"typeCode": "OH",
					"description": "Shipment is on hold",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-05-03",
					"time": "08:26:21",
					"typeCode": "WC",
					"description": "Shipment is out with courier for delivery",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					]
				},
				{
					"date": "2024-05-03",
					"time": "10:18:20",
					"typeCode": "OK",
					"description": "Delivered",
					"serviceArea": [
						{
							"code": "ZRH",
							"description": "Zurich-CH"
						}
					],
					"signedBy": "B Grumpy"
				}
			],
			"numberOfPieces": 1
		}
	]
}
"""
import json
import api_generate_str as ags

def main():
	FO = open("document.json", "r")
	docStr = FO.read()
	FO.close()
	generate_top_level(json.loads(docStr))

def generate_top_level(docJson):
	cu = docJson["url"]
	co = ""
	ags.s += docJson["desc"] + FORMAT_NEW_LINE + "\n"
	ags.s += FORMAT_URL.format(docJson["url"]) + "\n"
	ags.s += docJson["preface"] + "\n"
	for i in range(1, len(docJson["list"])+1):
		desiredJson = None
		for subJsonName in docJson["list"]:
			if docJson["list"][subJsonName]["ord"]==i:
				desiredJson = docJson["list"][subJsonName]
				desiredJson["name"] = subJsonName
				break
		if desiredJson: generate_h1_level(desiredJson, cu, co)

def generate_h1_level(docJson, cu, co):
	cu += docJson["url"]
	co += str(docJson["ord"])
	ags.s += FORMAT_H1.format(docJson["name"]) + "\n"
	ags.s += docJson["desc"] + FORMAT_NEW_LINE + "\n"
	ags.s += FORMAT_URL.format(cu) + "\n"
	ags.s += FORMAT_ORD.format(co) + "\n"
	for i in range(1, len(docJson["list"])+1):
		desiredJson = None
		for subJsonName in docJson["list"]:
			if docJson["list"][subJsonName]["ord"]==i:
				desiredJson = docJson["list"][subJsonName]
				desiredJson["name"] = subJsonName
				break
		if desiredJson: generate_h2_level(desiredJson, cu, co)

def generate_h2_level(docJson, cu, co):
	cu += docJson["url"]
	co += "_" + str(docJson["ord"])
	ags.s += FORMAT_H2.format(docJson["name"]) + "\n"
	ags.s += docJson["desc"] + FORMAT_NEW_LINE + "\n"
	ags.s += FORMAT_URL.format(cu) + "\n"
	ags.s += FORMAT_ORD.format(co) + "\n"
	for i in range(1, len(docJson["list"])+1):
		desiredJson = None
		for subJsonName in docJson["list"]:
			if docJson["list"][subJsonName]["ord"]==i:
				desiredJson = docJson["list"][subJsonName]
				desiredJson["name"] = subJsonName
				break
		if desiredJson: generate_h3_level(desiredJson, cu, co)

def generate_h3_level(docJson, cu, co):
	cu += docJson["url"]
	co += "_" + str(docJson["ord"])
	ags.s += FORMAT_H3.format(docJson["name"]) + "\n"
	ags.s += docJson["desc"] + FORMAT_NEW_LINE + "\n"
	if "pre" in docJson:
		if docJson["pre"]:
			ags.s += FORMAT_PRE.format(docJson["name"], docJson["name"].lower()) + "\n"
	ags.s += FORMAT_URL.format(cu) + "\n"
	ags.s += FORMAT_ORD.format(co) + "\n"
	# Request parameters.
	if "param" in docJson:
		ags.s += FORMAT_H4.format("Request Parameters") + "\n"
		for eachParamName in sorted(docJson["param"].keys()):
			eachParam = docJson["param"][eachParamName]
			eachParamDesc = eachParam["desc"]
			eachParamType = eachParam["type"]
			ags.s += FORMAT_PARAM.format(eachParamType, eachParamName, eachParamDesc)
			if "prec" in eachParam:
				ags.s += FORMAT_PARAM_PREC.format(eachParam["prec"])
			if "list" in eachParam:
				ags.s += FORMAT_NEW_LINE + "\n"
				for eachParamEnumKey in sorted(eachParam["list"].keys()):
					eachParamEnumValue = eachParam["list"][eachParamEnumKey]
					if eachParamEnumKey == "": eachParamEnumKey = "null"
					ags.s += FORMAT_PARAM_ENUM.format(eachParamEnumKey, eachParamEnumValue) + "\n"
			else:
				ags.s += "\n"
			ags.s += "\n"
	# Response.
	ags.s += FORMAT_H4.format("Response") + "\n"
	try:
		ags.s += docJson["res"]["desc"] + FORMAT_NEW_LINE + "\n"
	except:
		raise SystemError("{} has no attribute 'desc'".format(cu))
	ags.s += FORMAT_JSON.format(docJson["res"]["format"]) + "\n"
	# Example.
	if "example" in docJson:
		ags.s += FORMAT_H4.format("Example") + "\n"
		for eachExample in docJson["example"]:
			ags.s += FORMAT_H5.format("Request") + "\n"
			if "desc" in eachExample["req"]:
				ags.s += eachExample["req"]["desc"] + FORMAT_NEW_LINE + "\n"
			if "param" in eachExample["req"]:
				ags.s += FORMAT_URL.format(cu.format(**eachExample["req"]["param"])) + "\n"
			else:
				ags.s += FORMAT_URL.format(cu.split("?")[0]) + "\n"
			ags.s += FORMAT_H5.format("Response") + "\n"
			if "desc" in eachExample["res"]:
				ags.s += eachExample["res"]["desc"] + FORMAT_NEW_LINE + "\n"
			ags.s += FORMAT_JSON.format(eachExample["res"]["content"]) + "\n"
FORMAT_NEW_LINE = "  "
FORMAT_H1 = "# Trend API For {}.acfun.tv"
FORMAT_H2 = "## {}"
FORMAT_H3 = "### {}"
FORMAT_H4 = "#### {}"
FORMAT_H5 = "##### {}"
FORMAT_PARAM = "@_{}_ **{}**: {}"
FORMAT_PARAM_PREC = "<br>\n**Precondition:** {}"
FORMAT_PARAM_ENUM = "* **{}** - {}"
FORMAT_URL = "``` html\n{} <!--URL!-->\n```"
FORMAT_ORD = "``` html\n{} <!--ORD!-->\n```"
FORMAT_JSON = "``` json\n{}\n```"
FORMAT_PRE = "**Notice:** This API is partially pre-generated. Check [[Pre-generated APIs for {0}|TrendAPI:PreGenList#{1}]]"
if __name__ == '__main__':
	main()
	print(ags.s)

"""
tu
trend
"""
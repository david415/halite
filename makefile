
MESSAGE_JSON_DIR := src/messages
MESSAGE_JSON     := $(wildcard ${MESSAGE_JSON_DIR}/*.json)
C_MUSTACHE       := ${MESSAGE_JSON_DIR}/halite-c.mustache
MESSAGE_HEADDERS := convexstruct_types.h
MESSAGE_HEADDERS_DIR := message_headders

MESSAGE_JS     := messages.js
MESSAGE_JS_DIR := message_js


.PHONY: all clean distclean 
all:: messages


${MESSAGE_HEADDERS_DIR}:
	mkdir -p ${MESSAGE_HEADDERS_DIR}

${MESSAGE_JS_DIR}:
	mkdir -p ${MESSAGE_JS_DIR}

messages : ${MESSAGE_HEADDERS} ${MESSAGE_JS}


${MESSAGE_HEADDERS} : ${MESSAGE_HEADDERS_DIR}
	python src/python/messagebuilder.py --output-lang c --schema-files ${MESSAGE_JSON} --mustache-file ${C_MUSTACHE} > ${MESSAGE_HEADDERS_DIR}/${MESSAGE_HEADDERS}

${MESSAGE_JS} : ${MESSAGE_JS_DIR}
	python src/python/messagebuilder.py -o js -s ${MESSAGE_JSON} -m noop > ${MESSAGE_JS_DIR}/${MESSAGE_JS}


clean:: 
	-rm -rf *~ ${MESSAGE_HEADDERS_DIR} ${MESSAGE_JS_DIR}
	find src -name "*.pyc" | xargs rm

distclean:: clean


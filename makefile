
MESSAGE_JSON_DIR := src/messages
MESSAGE_JSON     := $(wildcard ${MESSAGE_JSON_DIR}/*.json)
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
	python src/python/messagebuilder.py c1 ${MESSAGE_JSON} > ${MESSAGE_HEADDERS_DIR}/${MESSAGE_HEADDERS}1
	python src/python/messagebuilder.py c ${MESSAGE_JSON} > ${MESSAGE_HEADDERS_DIR}/${MESSAGE_HEADDERS}

${MESSAGE_JS} : ${MESSAGE_JS_DIR}
	python src/python/messagebuilder.py js ${MESSAGE_JSON} > ${MESSAGE_JS_DIR}/${MESSAGE_JS}


clean:: 
	-rm -rf *~ ${MESSAGE_HEADDERS_DIR} ${MESSAGE_JS_DIR}
	find src -name "*.pyc" | xargs rm

distclean:: clean


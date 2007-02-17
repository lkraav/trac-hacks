/*
 * Copyright 2003, 2004  The Apache Software Foundation
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.xmlrpc.parser;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.apache.ws.commons.serialize.DOMBuilder;
import org.apache.xmlrpc.serializer.NodeSerializer;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;


/** A parser for DOM document.
 */
public class NodeParser extends ExtParser {
	private static final DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
	private final DOMBuilder builder = new DOMBuilder();

	protected String getTagName() {
		return NodeSerializer.DOM_TAG;
	}

	protected ContentHandler getExtHandler() throws SAXException {
		try {
			builder.setTarget(dbf.newDocumentBuilder().newDocument());
		} catch (ParserConfigurationException e) {
			throw new SAXException(e);
		}
		return builder;
	}

	public Object getResult() {
		return builder.getTarget();
	}
}

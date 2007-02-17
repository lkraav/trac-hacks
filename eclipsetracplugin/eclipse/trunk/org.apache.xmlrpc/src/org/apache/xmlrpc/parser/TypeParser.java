/*
 * Copyright 1999,2005 The Apache Software Foundation.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *      http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.xmlrpc.parser;

import org.apache.xmlrpc.XmlRpcException;
import org.xml.sax.ContentHandler;


/** Interface of a SAX handler parsing a single parameter or
 * result object.
 */
public interface TypeParser extends ContentHandler {
	/** Returns the parsed object.
	 * @return The parameter or result object.
	 * @throws XmlRpcException Creating the result object failed.
	 * @throws IllegalStateException The method was invoked before
	 * {@link org.xml.sax.ContentHandler#endDocument}.
	 */
	public Object getResult() throws XmlRpcException;
}

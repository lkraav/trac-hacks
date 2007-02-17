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
package org.apache.xmlrpc.client;




/** Default implementation of a HTTP transport factory, based on the
 * {@link java.net.HttpURLConnection} class.
 */
public class XmlRpcSunHttpTransportFactory extends XmlRpcTransportFactoryImpl {
	private final XmlRpcSunHttpTransport HTTP_TRANSPORT;

	/** Creates a new factory, which creates transports for the given client.
	 * @param pClient The client, which is operating the factory.
	 */
	public XmlRpcSunHttpTransportFactory(XmlRpcClient pClient) {
		super(pClient);
		HTTP_TRANSPORT = new XmlRpcSunHttpTransport(pClient);
	 }

	public XmlRpcTransport getTransport() { return HTTP_TRANSPORT; }
}

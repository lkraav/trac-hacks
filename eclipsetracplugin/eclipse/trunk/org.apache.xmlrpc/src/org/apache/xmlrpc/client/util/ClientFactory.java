/*
 * Copyright 1999,2006 The Apache Software Foundation.
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
package org.apache.xmlrpc.client.util;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.common.TypeConverter;
import org.apache.xmlrpc.common.TypeConverterFactory;
import org.apache.xmlrpc.common.TypeConverterFactoryImpl;


/**
 * <p>The {@link ClientFactory} is a useful tool for simplifying the
 * use of Apache XML-RPC. The rough idea is as follows: All XML-RPC
 * handlers are implemented as interfaces. The server uses the actual
 * implementation. The client uses the {@link ClientFactory} to
 * obtain an implementation, which is based on running XML-RPC calls.</p>
 */
public class ClientFactory {
    private final XmlRpcClient client;
    private final TypeConverterFactory typeConverterFactory;
    private boolean objectMethodLocal;

    /** Creates a new instance.
     * @param pClient A fully configured XML-RPC client, which is
     *   used internally to perform XML-RPC calls.
     * @param pTypeConverterFactory Creates instances of {@link TypeConverterFactory},
     *   which are used to transform the result object in its target representation.
     */
    public ClientFactory(XmlRpcClient pClient, TypeConverterFactory pTypeConverterFactory) {
        typeConverterFactory = pTypeConverterFactory;
        client = pClient;
    }

    /** Creates a new instance. Shortcut for
     * <pre>
     *   new ClientFactory(pClient, new TypeConverterFactoryImpl());
     * </pre>
     * @param pClient A fully configured XML-RPC client, which is
     *   used internally to perform XML-RPC calls.
     * @see TypeConverterFactoryImpl
     */
    public ClientFactory(XmlRpcClient pClient) {
        this(pClient, new TypeConverterFactoryImpl());
    }

    /** Returns the factories client.
     */
    public XmlRpcClient getClient() {
        return client;
    }

    /** Returns, whether a method declared by the {@link Object
     * Object class} is performed by the local object, rather than
     * by the server. Defaults to true.
     */
    public boolean isObjectMethodLocal() {
        return objectMethodLocal;
    }

    /** Sets, whether a method declared by the {@link Object
     * Object class} is performed by the local object, rather than
     * by the server. Defaults to true.
     */
    public void setObjectMethodLocal(boolean pObjectMethodLocal) {
        objectMethodLocal = pObjectMethodLocal;
    }

    /** Creates an object, which is implementing the given interface.
     * The objects methods are internally calling an XML-RPC server
     * by using the factories client.
     */
    public Object newInstance(Class pClass) {
        return newInstance(Thread.currentThread().getContextClassLoader(), pClass);
    }

    /** Creates an object, which is implementing the given interface.
     * The objects methods are internally calling an XML-RPC server
     * by using the factories client.
     */
    public Object newInstance(ClassLoader pClassLoader, final Class pClass) {
        return Proxy.newProxyInstance(pClassLoader, new Class[]{pClass}, new InvocationHandler(){
            public Object invoke(Object pProxy, Method pMethod, Object[] pArgs) throws Throwable {
                if (isObjectMethodLocal()  &&  pMethod.getDeclaringClass().equals(Object.class)) {
                    return pMethod.invoke(pProxy, pArgs);
                }
                String methodName = pClass.getName() + "." + pMethod.getName();
                Object result = client.execute(methodName, pArgs);
                TypeConverter typeConverter = typeConverterFactory.getTypeConverter(pMethod.getReturnType());
                return typeConverter.convert(result);
            }
        });
    }
}

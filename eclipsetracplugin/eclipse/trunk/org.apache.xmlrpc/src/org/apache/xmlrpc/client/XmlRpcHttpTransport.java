package org.apache.xmlrpc.client;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.XmlRpcRequest;
import org.apache.xmlrpc.util.HttpUtil;
import org.xml.sax.SAXException;


/** Abstract base implementation of an HTTP transport. Base class for the
 * concrete implementations, like {@link org.apache.xmlrpc.client.XmlRpcSunHttpTransport},
 * or {@link org.apache.xmlrpc.client.XmlRpcCommonsTransport}.
 */
public abstract class XmlRpcHttpTransport extends XmlRpcStreamTransport {
    protected class ByteArrayReqWriter implements ReqWriter {
        private final ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ByteArrayReqWriter(XmlRpcRequest pRequest)
                throws XmlRpcException, IOException, SAXException {
            new ReqWriterImpl(pRequest).write(baos);
        }

        protected int getContentLength() {
            return baos.size();
        }

        public void write(OutputStream pStream) throws IOException {
            try {
                baos.writeTo(pStream);
                pStream.close();
                pStream = null;
            } finally {
                if (pStream != null) { try { pStream.close(); } catch (Throwable ignore) {} }
            }
        }
    }

	private String userAgent;

	/** The user agent string.
	 */
	public static final String USER_AGENT = "Apache XML RPC 3.0";

	protected XmlRpcHttpTransport(XmlRpcClient pClient, String pUserAgent) {
		super(pClient);
		userAgent = pUserAgent;
	}

	protected String getUserAgent() { return userAgent; }

	protected abstract void setRequestHeader(String pHeader, String pValue);

	protected void setCredentials(XmlRpcHttpClientConfig pConfig)
			throws XmlRpcClientException {
		String auth;
		try {
			auth = HttpUtil.encodeBasicAuthentication(pConfig.getBasicUserName(),
													  pConfig.getBasicPassword(),
													  pConfig.getBasicEncoding());
		} catch (UnsupportedEncodingException e) {
			throw new XmlRpcClientException("Unsupported encoding: " + pConfig.getBasicEncoding(), e);
		}
		if (auth != null) {
			setRequestHeader("Authorization", "Basic " + auth);
		}
	}

	protected void setContentLength(int pLength) {
		setRequestHeader("Content-Length", Integer.toString(pLength));
	}

	protected void setCompressionHeaders(XmlRpcHttpClientConfig pConfig) {
		if (pConfig.isGzipCompressing()) {
			setRequestHeader("Content-Encoding", "gzip");
		}
		if (pConfig.isGzipRequesting()) {
			setRequestHeader("Accept-Encoding", "gzip");
		}
	}

	protected void initHttpHeaders(XmlRpcRequest pRequest) throws XmlRpcClientException {
		XmlRpcHttpClientConfig config = (XmlRpcHttpClientConfig) pRequest.getConfig();
		setRequestHeader("Content-Type", "text/xml");
		setRequestHeader("User-Agent", getUserAgent());
		setCredentials(config);
		setCompressionHeaders(config);
	}

	public Object sendRequest(XmlRpcRequest pRequest) throws XmlRpcException {
		initHttpHeaders(pRequest);
		return super.sendRequest(pRequest);
	}

	protected boolean isUsingByteArrayOutput(XmlRpcHttpClientConfig pConfig) {
		return !pConfig.isEnabledForExtensions()
			|| !pConfig.isContentLengthOptional();
	}

	protected ReqWriter newReqWriter(XmlRpcRequest pRequest)
			throws XmlRpcException, IOException, SAXException {
		final XmlRpcHttpClientConfig config = (XmlRpcHttpClientConfig) pRequest.getConfig();
        if (isUsingByteArrayOutput(config)) {
            ByteArrayReqWriter reqWriter = new ByteArrayReqWriter(pRequest);
            setContentLength(reqWriter.getContentLength());
            if (isCompressingRequest(config)) {
                return new GzipReqWriter(reqWriter);
            }
            return reqWriter;
		} else {
			return super.newReqWriter(pRequest);
		}
	}
}

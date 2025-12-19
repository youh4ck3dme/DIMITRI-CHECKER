// #region agent log
fetch('http://127.0.0.1:7243/ingest/6df07fcf-4b08-4bfb-a01f-2db77f7258f1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'main.jsx:1',message:'App starting',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
// #endregion
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// #region agent log
fetch('http://127.0.0.1:7243/ingest/6df07fcf-4b08-4bfb-a01f-2db77f7258f1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'main.jsx:10',message:'Before render',data:{hasRoot:!!document.getElementById('root')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
// #endregion

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)


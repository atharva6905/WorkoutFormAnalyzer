import { BrowserRouter, Route, Routes } from 'react-router-dom';

import ResultPage from './pages/ResultPage';
import UploadPage from './pages/UploadPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/results/:analysisId" element={<ResultPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

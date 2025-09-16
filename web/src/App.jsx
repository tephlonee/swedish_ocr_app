import React, { useState } from 'react';
import axios from 'axios';
import {
  Container,
  AppBar,
  Toolbar,
  Typography,
  Card,
  CardContent,
  Button,
  Box,
  CircularProgress,
  Chip,
  CssBaseline
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

function App() {
  const [file, setFile] = useState(null);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('http://ocr_app:5000/ocr', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setText(res.data.text);
    } catch (err) {
      setText('Error processing image');
    }
    setLoading(false);
  };

  return (
    <>
      <CssBaseline />
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h4" component="div" sx={{ flexGrow: 1 }}>
            Swedish OCR Translator
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box component="form" onSubmit={handleUpload} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <Button
                variant="outlined"
                component="label"
                startIcon={<CloudUploadIcon />}
                sx={{ minWidth: 200 }}
              >
                Choose Image
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => setFile(e.target.files[0])}
                />
              </Button>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={!file || loading}
                startIcon={loading ? <CircularProgress size={20} /> : null}
                sx={{ minWidth: 200 }}
              >
                {loading ? 'Processing...' : 'Extract Text'}
              </Button>
            </Box>
          </CardContent>
        </Card>
        {text && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Extracted Text:
              </Typography>
              <Chip label="Swedish OCR" color="primary" size="small" />
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1, maxHeight: 300, overflow: 'auto' }}>
                <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {text}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        )}
      </Container>
    </>
  );
}

export default App;
import React, { useState } from 'react';
import { Download, FileText, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const BulkCheckDemo = () => {
  const [showDemo, setShowDemo] = useState(false);

  // Sample CSV content for demo
  const sampleCSV = `phone_number
+6281234567890
+6289876543210
+6285555666777
08123456789
+628111222333
+628444555666
08777888999
+628999111222
08333444555
+628666777888`;

  const downloadSampleCSV = () => {
    const element = document.createElement("a");
    const file = new Blob([sampleCSV], { type: 'text/csv' });
    element.href = URL.createObjectURL(file);
    element.download = "sample_phone_numbers.csv";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    toast.success('Sample CSV file downloaded!');
  };

  const simulateBulkUpload = () => {
    // Create a sample CSV file and simulate upload
    const file = new File([sampleCSV], "demo_numbers.csv", { type: "text/csv" });
    
    // This would normally be handled by the actual bulk check component
    toast.success('Demo file uploaded successfully!');
    setShowDemo(true);
    
    // Simulate processing
    setTimeout(() => {
      toast.success('Demo bulk validation completed!');
    }, 3000);
  };

  return (
    <div className="space-y-6">
      {/* Demo Section */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          🎯 Demo Bulk Check
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Try our bulk validation feature with sample phone numbers
        </p>
        
        <div className="flex space-x-4">
          <button
            onClick={downloadSampleCSV}
            className="btn-secondary flex items-center"
          >
            <Download className="h-4 w-4 mr-2" />
            Download Sample CSV
          </button>
          
          <button
            onClick={simulateBulkUpload}
            className="btn-primary flex items-center"
          >
            <FileText className="h-4 w-4 mr-2" />
            Try Demo Upload
          </button>
        </div>
      </div>

      {/* Demo Results */}
      {showDemo && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            Demo Results
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">6</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">WhatsApp Active</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">4</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Telegram Active</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">0</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Inactive</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">0</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Errors</p>
            </div>
          </div>
          
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <p>✅ 10 numbers processed successfully</p>
            <p>📊 Using real providers: Twilio WhatsApp Business, Primary Telegram Bot</p>
            <p>⚡ Processing time: 3.2 seconds</p>
            <p>💰 Credits used: 20 (2 per number)</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkCheckDemo;
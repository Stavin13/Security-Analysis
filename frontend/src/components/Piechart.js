import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

const PieChartComponent = ({ data, options = {} }) => {
  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  };

  const mergedOptions = { ...defaultOptions, ...options };

  if (!data || !data.datasets) {
    return <div>No data available</div>;
  }

  return (
    <div style={{ height: '300px' }}>
      <Pie data={data} options={mergedOptions} />
    </div>
  );
};

export default PieChartComponent;
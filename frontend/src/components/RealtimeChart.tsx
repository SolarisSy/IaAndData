'use client';

import { useState, useEffect, useRef } from 'react';
import { Line } from 'react-chartjs-2';

// O ChartJS já foi registrado na página principal, então não precisamos registrar aqui novamente.

type RealtimeChartProps = {
  ticker: string;
  isActive: boolean; // <-- Nova propriedade para controlar a atividade
};

type IntradayData = {
  labels: string[];
  price: number[];
  vwap: number[];
};

const RealtimeChart = ({ ticker, isActive }: RealtimeChartProps) => {
  const [chartData, setChartData] = useState<IntradayData>({ labels: [], price: [], vwap: [] });
  const [status, setStatus] = useState('Aguardando ativação...');
  const chartRef = useRef(null);

  useEffect(() => {
    // Se o gráfico não estiver ativo, não faça nada e limpe qualquer intervalo existente.
    if (!isActive) {
      setStatus('Inativo');
      return;
    }

    const fetchData = async () => {
      setStatus('Carregando dados...');
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/v1/intraday/${ticker}`);
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Erro ao buscar dados.');
        }

        const data: IntradayData = await response.json();
        setChartData(data);
        setStatus(`Dados para ${ticker} atualizados`);
      } catch (error: unknown) { // Alterado de 'any' para 'unknown'
        console.error("Erro no fetch:", error);
        let errorMessageText = "Erro ao buscar dados.";
        if (error instanceof Error) {
          errorMessageText = `Erro: ${error.message}`;
        }
        setStatus(errorMessageText);
      }
    };

    fetchData(); // Busca inicial
    const intervalId = setInterval(fetchData, 60000); // Atualiza a cada 60 segundos

    // Limpa o intervalo quando o componente é desmontado OU quando se torna inativo
    return () => {
      console.log(`Limpando intervalo para o ticker: ${ticker}`);
      clearInterval(intervalId);
    }
  }, [ticker, isActive]); // Re-executa o efeito se o ticker ou o estado de ativação mudar

  const data = {
    labels: chartData.labels,
    datasets: [
      {
        label: `Preço (${ticker})`,
        data: chartData.price,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        yAxisID: 'y',
      },
      {
        label: 'VWAP (Indicador Preditivo)',
        data: chartData.vwap,
        borderColor: 'rgb(255, 159, 64)',
        borderDash: [5, 5],
        yAxisID: 'y',
      },
    ],
  };

  const options = {
    responsive: true,
    animation: {
      duration: 400,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#fff',
        }
      },
      title: {
        display: true,
        text: `Gráfico Intraday (1 min) com VWAP - ${status}`,
        color: '#fff',
        font: { size: 16 }
      },
    },
    scales: {
      x: {
        ticks: { color: '#ddd' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        ticks: { color: '#ddd' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
    },
  };

  return <Line ref={chartRef} options={options} data={data} />;
};

export default RealtimeChart;

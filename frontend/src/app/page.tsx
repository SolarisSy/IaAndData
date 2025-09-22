'use client';

import { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions, // Importado para tipagem forte
  LegendItem,   // Importado para tipagem forte
  ChartData as ChartJSData // Importado e renomeado para evitar conflito
} from 'chart.js';
import RealtimeChart from '@/components/RealtimeChart'; 

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Define a type for our chart data structure
type ChartData = {
  historical: { date: string; close: number }[];
  cone: {
    date: string;
    predicted_price: number;
    upper_bound_95: number;
    lower_bound_95: number;
    upper_bound_70: number;
    lower_bound_70: number;
  }[];
  analysis: string;
};

// --- Novo: Estrutura para mensagens do chat ---
interface Message {
  sender: 'user' | 'ia';
  text: string;
  chartData?: ChartData | null;
  realtimeTicker?: string | null;
}

// --- Novo: Tipagem para o corpo da requisição ---
interface QueryRequestBody {
  question: string;
  session_id: string;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]); // Armazena todo o chat
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  // Gera um ID de sessão único quando o componente é montado
  useEffect(() => {
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`);
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    
    // Variável de ambiente para a URL da API
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

    const userMessage: Message = { sender: 'user', text: query };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setQuery('');

    // --- Lógica de Roteamento de Requisição ---
    const keywords = ['previsão', 'projeção', 'volatilidade', 'cone', 'prever', 'futuro'];
    const containsKeyword = keywords.some(keyword => query.toLowerCase().includes(keyword));
    const tickerMatch = query.match(/([A-Z0-9]+\.SA)/i);

    let apiEndpoint = `${API_BASE_URL}/api/v1/query`;
    let requestBody: QueryRequestBody | null = { question: query, session_id: sessionId };
    let requestMethod = 'POST';

    // Se a pergunta parece ser sobre projeção e contém um ticker, use o endpoint direto.
    if (containsKeyword && tickerMatch) {
      const ticker = tickerMatch[0].toUpperCase();
      apiEndpoint = `${API_BASE_URL}/api/v1/volatility-cone/${ticker}`;
      requestBody = null; // GET request não tem corpo
      requestMethod = 'GET';
      console.log(`Chamada direta para o projeção: ${apiEndpoint}`);
    } else {
      console.log(`Chamada para o agente de IA: ${apiEndpoint}`);
    }
    // --- Fim da Lógica ---

    try {
      const fetchOptions: RequestInit = {
        method: requestMethod,
        headers: {
          'Content-Type': 'application/json',
        },
      };
      
      if (requestBody) {
        fetchOptions.body = JSON.stringify(requestBody);
      }

      const response = await fetch(apiEndpoint, fetchOptions);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erro na API: ${response.statusText}`);
      }

      const data = await response.json();
      const iaMessage: Message = { sender: 'ia', text: '' };

      if (data.chart_data) {
        iaMessage.chartData = data.chart_data;
        iaMessage.text = data.chart_data.analysis;
      } else {
        iaMessage.text = data.answer;
        // Se a resposta não for um gráfico, mas contiver um ticker, ofereça o gráfico em tempo real
        const tickerMatchInAnswer = iaMessage.text.match(/([A-Z0-9]+\.SA)/i);
        if (tickerMatchInAnswer) {
          iaMessage.realtimeTicker = tickerMatchInAnswer[0].toUpperCase();
        }
      }
      
      setMessages(prevMessages => [...prevMessages, iaMessage]);

    } catch (error: unknown) { // Alterado de 'any' para 'unknown'
      console.error("Falha ao buscar dados da API", error);
      
      let errorMessageText = "Desculpe, ocorreu um erro inesperado.";
      if(error instanceof Error) {
        errorMessageText = `Desculpe, ocorreu um erro: ${error.message}`;
      }

      const errorMessage: Message = {
        sender: 'ia',
        text: errorMessageText
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateChartConfig = (data: ChartData): ChartJSData<'line'> => { // Adicionada tipagem de retorno
    const allLabels = [...data.historical.map(p => p.date.split('T')[0]), ...data.cone.map(p => p.date)];
    
    const historicalClose = data.historical.map(p => p.close);
    const predictedLine = [...Array(data.historical.length).fill(null), ...data.cone.map(p => p.predicted_price)];
    
    // Connect the historical data to the prediction
    predictedLine[data.historical.length - 1] = historicalClose[historicalClose.length - 1];

    return {
      labels: allLabels,
      datasets: [
        {
          label: 'Preço Histórico',
          data: historicalClose,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          tension: 0.1,
          pointRadius: 1,
        },
        {
          label: 'Previsão (Tendência Linear)',
          data: predictedLine,
          borderColor: 'rgb(255, 159, 64)',
          borderDash: [5, 5],
          tension: 0.1,
          pointRadius: 1,
        },
        {
          label: 'Cone de Incerteza (95%)',
          data: [...Array(data.historical.length).fill(null), ...data.cone.map(p => p.upper_bound_95)],
          borderColor: 'rgba(255, 99, 132, 0.2)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          fill: '+1', // Preenche até o próximo dataset com 'fill: false'
          tension: 0.4,
          pointRadius: 0,
        },
        {
          label: 'Cone de Incerteza (95%) Lower', // Label diferente para evitar conflito na legenda
          data: [...Array(data.historical.length).fill(null), ...data.cone.map(p => p.lower_bound_95)],
          borderColor: 'rgba(255, 99, 132, 0.2)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          fill: false,
          tension: 0.4,
          pointRadius: 0,
        },
         {
          label: 'Cone de Incerteza (70%)',
          data: [...Array(data.historical.length).fill(null), ...data.cone.map(p => p.upper_bound_70)],
          borderColor: 'rgba(75, 192, 192, 0.2)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          fill: '+1', // Preenche até o próximo dataset com 'fill: false'
          tension: 0.4,
          pointRadius: 0,
        },
        {
          label: 'Cone de Incerteza (70%) Lower', // Label diferente
          data: [...Array(data.historical.length).fill(null), ...data.cone.map(p => p.lower_bound_70)],
          borderColor: 'rgba(75, 192, 192, 0.2)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          fill: false,
          tension: 0.4,
          pointRadius: 0,
        },
      ],
    };
  };

  const chartOptions: ChartOptions<'line'> = { // Adicionada tipagem forte
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
            color: '#fff',
            // Filter out duplicate legend items for the fill
            filter: function(legendItem: LegendItem) { // Adicionada tipagem e removido 'chartData' não usado
              return !legendItem.text.includes('Lower');
            }
        }
      },
      title: {
        display: true,
        text: 'Projeção de Volatilidade e Cone de Incerteza',
        color: '#fff',
        font: {
            size: 18
        }
      },
    },
    scales: {
        x: {
            ticks: { color: '#ddd' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
        },
        y: {
            ticks: { color: '#ddd' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
        }
    }
  };


  return (
    <main className="flex min-h-screen flex-col items-center bg-gray-900 text-white p-8">
      <div className="w-full max-w-4xl flex flex-col h-screen">
        <h1 className="text-4xl font-bold text-center mb-6 shrink-0">
          IaAndData 📈
        </h1>

        {/* --- Banner Impacto / Prova de Capacidade --- */}
        {(() => {
          const totalRealtimeCharts = messages.filter(m => !!m.realtimeTicker).length;
          const lastRealtimeIndex = messages.map(m => !!m.realtimeTicker).lastIndexOf(true);
          const hasActiveRealtime = lastRealtimeIndex !== -1; // apenas o último fica ativo
          const activeRpm = hasActiveRealtime ? 1 : 0; // 1 req/min por ativo ativo (VWAP)
          const sessionMsgs = messages.length;

          return (
            <div className="mb-4 rounded-xl border border-gray-700 bg-gradient-to-br from-blue-900/40 via-indigo-900/30 to-purple-900/30 backdrop-blur px-4 py-3 shadow-lg">
              <div className="flex flex-col gap-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm md:text-base font-semibold text-indigo-200">
                    Esta plataforma orquestra IA + ETL + Estatística para transformar dados do mercado brasileiro em decisões.
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-xs text-emerald-300">Ambiente Ativo</span>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-gray-200">
                  <div className="rounded-lg border border-gray-700/60 bg-gray-800/40 p-3">
                    <div className="font-semibold text-indigo-300 mb-1">Telemetria em Tempo Real</div>
                    <div className="flex flex-col gap-1 text-gray-300">
                      <div>• Atualização VWAP: 1×/min por ativo ativo</div>
                      <div>• Ativos monitorados (sessão): {totalRealtimeCharts}</div>
                      <div>• Ativos ativos agora: {hasActiveRealtime ? 1 : 0}</div>
                      <div>• Requisições/min (estimado): {activeRpm}</div>
                    </div>
                  </div>
                  <div className="rounded-lg border border-gray-700/60 bg-gray-800/40 p-3">
                    <div className="font-semibold text-indigo-300 mb-1">Cobertura & Inteligência</div>
                    <div className="flex flex-col gap-1 text-gray-300">
                      <div>• Fonte de dados: Yahoo Finance (via yfinance)</div>
                      <div>• Persistência: Supabase (PostgreSQL)</div>
                      <div>• Projeções: Cone de Volatilidade (histórico até 252d)</div>
                      <div>• Memória de conversa por sessão (mensagens: {sessionMsgs})</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })()}

        {/* --- Área de Chat Rolável --- */}
        <div className="flex-grow overflow-y-auto mb-4 p-4 bg-gray-800 rounded-lg">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-gray-500">
              Comece a conversa fazendo uma pergunta abaixo.
            </div>
          )}
          {messages.map((msg, index) => (
            <RenderMessage 
              key={index} 
              msg={msg} 
              index={index} 
              messages={messages} 
              chartOptions={chartOptions}
              generateChartConfig={generateChartConfig}
            />
          ))}
           {isLoading && (
            <div className="flex justify-start">
              <div className="p-4 rounded-lg bg-gray-700">
                <p className="text-gray-400 italic">Analisando...</p>
              </div>
            </div>
          )}
        </div>

        {/* --- Formulário de Input Fixo na Base --- */}
        <form onSubmit={handleSubmit} className="w-full shrink-0">
          <div className="flex flex-col gap-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Pergunte sobre dados financeiros..."
              className="p-4 rounded-lg bg-gray-800 border border-gray-700 focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg disabled:bg-gray-600 transition"
              disabled={isLoading || !query}
            >
              {isLoading ? 'Enviando...' : 'Perguntar'}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

// --- Componente de Renderização de Mensagem (Refatorado para fora do componente Home) ---
function RenderMessage({ msg, index, messages, chartOptions, generateChartConfig }: {
  msg: Message;
  index: number;
  messages: Message[];
  chartOptions: ChartOptions<'line'>; // Alterado de 'any' para tipo específico
  generateChartConfig: (data: ChartData) => ChartJSData<'line'>; // Alterado de 'any' para tipo específico
}) {
  // Encontra o índice da última mensagem no chat que possui um gráfico em tempo real
  const lastMessageWithRealtimeChartIndex = messages.map(m => !!m.realtimeTicker).lastIndexOf(true);

  return (
    <div key={index} className={`mb-6 flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`p-4 rounded-lg max-w-xl ${msg.sender === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
        <p className="text-gray-100 whitespace-pre-wrap">{msg.text}</p>
        
        {msg.chartData && (
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-600 mt-4">
            <Line options={chartOptions} data={generateChartConfig(msg.chartData)} />
          </div>
        )}
        
        {msg.realtimeTicker && (
           <div className="bg-gray-800 p-4 rounded-lg border border-gray-600 mt-4">
             <h2 className="text-lg font-semibold mb-3 text-center">
               Monitoramento Intraday: {msg.realtimeTicker}
             </h2>
             <RealtimeChart 
               ticker={msg.realtimeTicker} 
               isActive={index === lastMessageWithRealtimeChartIndex} // <-- Passa a propriedade
             />
           </div>
        )}
      </div>
    </div>
  );
}

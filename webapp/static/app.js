document.addEventListener('DOMContentLoaded', () => {
    const ctx = document.getElementById('gexChart').getContext('2d');
    let gexChart;

    // UI Elements
    const elPrice = document.getElementById('price');
    const elPriceArrow = document.getElementById('price-arrow');
    const elTotal = document.getElementById('total-gex');
    const elExpiryDate = document.getElementById('expiry-date'); // Input
    const elLastUpdate = document.getElementById('last-update');
    const elStatusDot = document.getElementById('status-dot');
    const elRefreshRate = document.getElementById('refresh-rate');
    const elTickerInput = document.getElementById('ticker-input');
    const elDisplayTicker = document.getElementById('display-ticker');

    let refreshInterval;
    let previousPrice = null;
    let previousSignal = null;
    let alertsEnabled = true;
    let speechEnabled = false; // Disabled speech alerts
    let wallProximityThreshold = 10; // points

    // Event Listener for Date Change
    // We remove the interval loop from main scope to control it better? 
    // Or just let the interval run. Interval hits fetchData, which reads input.
    // Explicit change triggers immediate fetch.
    elExpiryDate.addEventListener('change', () => {
        fetchData();
    });

    // Refresh Rate Listener
    elRefreshRate.addEventListener('change', () => {
        setupAutoRefresh();
    });

    // Ticker Input Listener
    elTickerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            fetchData();
            setupAutoRefresh();
        }
    });

    // Request notification permission on load
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }

    // Speech synthesis
    function speak(text) {
        if (!speechEnabled || !('speechSynthesis' in window)) return;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.1;
        utterance.pitch = 1;
        utterance.volume = 0.8;
        speechSynthesis.speak(utterance);
    }

    // Show notification
    function notify(title, body, urgent = false) {
        if (!alertsEnabled) return;

        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: body,
                tag: urgent ? 'urgent' : 'info'
            });
        }

        // Speech alert
        if (urgent) {
            speak(title + '. ' + body);
        }
    }

    function setupAutoRefresh() {
        if (refreshInterval) clearInterval(refreshInterval);
        const rate = parseInt(elRefreshRate.value);
        if (rate > 0) {
            refreshInterval = setInterval(fetchData, rate);
        }
    }

    // Register Plugin (Safety)
    if (window['chartjs-plugin-annotation']) {
        Chart.register(window['chartjs-plugin-annotation']);
    }

    // === VISUAL TRADE ALERT SYSTEM ===
    let currentAlertSignal = null;

    function showTradeAlert(signal, ticker) {
        const banner = document.getElementById('trade-alert-banner');
        const message = document.getElementById('alert-message');

        // Only show for actionable signals
        if (!signal.includes('BUY') && !signal.includes('SELL')) {
            dismissAlert();
            return;
        }

        // Don't re-show same alert
        if (currentAlertSignal === signal) return;
        currentAlertSignal = signal;

        // Set message and style
        if (signal.includes('BUY')) {
            message.innerText = `🚀 ${ticker} BUY SIGNAL ACTIVE - ${signal}`;
            banner.className = 'trade-alert-banner buy';
        } else if (signal.includes('SELL')) {
            message.innerText = `⚡ ${ticker} SELL SIGNAL ACTIVE - ${signal}`;
            banner.className = 'trade-alert-banner sell';
        }

        banner.style.display = 'block';

        // Add pulsing to entry signal box
        const signalBox = document.getElementById('strategy-signal');
        if (signalBox) {
            signalBox.classList.add('signal-highlight');
        }
    }

    window.dismissAlert = function () {
        const banner = document.getElementById('trade-alert-banner');
        banner.style.display = 'none';
        currentAlertSignal = null;

        // Remove pulsing
        const signalBox = document.getElementById('strategy-signal');
        if (signalBox) {
            signalBox.classList.remove('signal-highlight');
        }
    }

    function initChart() {
        gexChart = new Chart(ctx, {
            type: 'bar', // Explicitly set main type to bar again just in case
            data: {
                labels: [],
                datasets: [
                    {
                        type: 'bar',
                        label: 'Gamma Exposure ($B)',
                        data: [],
                        backgroundColor: [],
                        borderWidth: 0,
                        borderRadius: 4,
                        barPercentage: 0.6,
                        categoryPercentage: 0.8,
                        order: 2
                    },
                    {
                        type: 'line',
                        label: 'Spot Line',
                        data: [],
                        borderColor: '#ff9900',
                        borderWidth: 3,
                        pointRadius: 0,
                        borderDash: [],
                        order: 1 // Top z-index
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                interaction: {
                    mode: 'index',
                    intersect: false,
                    axis: 'x'
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        position: 'nearest',
                        backgroundColor: 'rgba(20, 20, 22, 0.9)',
                        titleColor: '#00e5ff',
                        callbacks: {
                            label: function (context) {
                                if (context.dataset.type === 'line' && context.dataset.label === 'Spot Line') return '';
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) {
                                    if (context.dataset.label.includes('Gamma')) {
                                        label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y) + 'B';
                                    } else {
                                        label += new Intl.NumberFormat('en-US').format(context.parsed.y);
                                    }
                                }
                                return label;
                            },
                            afterBody: function (context) {
                                // Add OI and Volume here
                                const idx = context[0].dataIndex;
                                const chart = context[0].chart;
                                const oi = chart.data.customData ? chart.data.customData.oi[idx] : 0;
                                const vol = chart.data.customData ? chart.data.customData.volume[idx] : 0;

                                return [
                                    'OI: ' + new Intl.NumberFormat('en-US').format(oi),
                                    'Vol: ' + new Intl.NumberFormat('en-US').format(vol)
                                ];
                            }
                        }
                    },
                    annotation: {
                        annotations: {}
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#666' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: '#222' },
                        ticks: { color: '#666' }
                    }
                }
            }
        });
    }

    async function fetchData() {
        // Status Indication
        elStatusDot.style.backgroundColor = '#ffff00'; // Yellow fetching
        try {
            // Build URL with date param if selected
            let url = '/api/gex';
            const params = new URLSearchParams();
            if (elExpiryDate.value) params.append('date', elExpiryDate.value);
            if (elTickerInput.value) params.append('ticker', elTickerInput.value);

            if (params.toString()) url += '?' + params.toString();

            const response = await fetch(url);
            if (!response.ok) throw new Error('Network response');
            const data = await response.json();
            updateDashboard(data);
            elStatusDot.style.backgroundColor = '#00ff9d';
            elStatusDot.classList.add('pulsing');
        } catch (error) {
            console.error(error);
            elStatusDot.style.backgroundColor = '#ff3366';
            elStatusDot.classList.remove('pulsing');
        }
    }

    function updateDashboard(data) {
        // ... stats update ...
        elPrice.innerText = '$' + data.price.toFixed(2);

        // Price Trend
        if (previousPrice !== null) {
            if (data.price > previousPrice) {
                elPriceArrow.innerText = '▲';
                elPriceArrow.style.color = '#00ff9d';
            } else if (data.price < previousPrice) {
                elPriceArrow.innerText = '▼';
                elPriceArrow.style.color = '#ff3366';
            }
        }
        previousPrice = data.price;

        // === ALERTS SYSTEM ===
        // 1. Signal Change Alert
        if (data.strategy && data.strategy.signal) {
            const currentSignal = data.strategy.signal.text;
            if (previousSignal && currentSignal !== previousSignal) {
                // Signal changed
                if (currentSignal.includes('BUY')) {
                    notify('🟢 BUY SIGNAL', `Entry signal triggered for ${data.ticker}`, true);
                } else if (currentSignal.includes('SELL')) {
                    notify('🔴 SELL SIGNAL', `Entry signal triggered for ${data.ticker}`, true);
                } else if (currentSignal.includes('CAUTION')) {
                    notify('⚠️ CAUTION', currentSignal, false);
                }
            }
            previousSignal = currentSignal;
        }

        // 2. Wall Proximity Alert
        if (data.call_wall && Math.abs(data.price - data.call_wall) <= wallProximityThreshold) {
            const distance = (data.call_wall - data.price).toFixed(2);
            notify('⚠️ CALL WALL NEARBY', `Price is ${distance} points from Call Wall at ${data.call_wall}`, true);
        }
        if (data.put_wall && Math.abs(data.price - data.put_wall) <= wallProximityThreshold) {
            const distance = (data.price - data.put_wall).toFixed(2);
            notify('⚠️ PUT WALL NEARBY', `Price is ${distance} points from Put Wall at ${data.put_wall}`, true);
        }

        if (data.ticker) elDisplayTicker.innerText = data.ticker;
        elTotal.innerText = '$' + data.total_gex.toFixed(2) + 'B';
        elTotal.className = 'stat-value ' + (data.total_gex >= 0 ? 'positive' : 'negative');
        elExpiryDate.value = data.expiry; // Keep synced
        elLastUpdate.innerText = new Date().toLocaleTimeString();

        // Strategy Panel
        if (data.strategy) {
            // Signal
            const elSignal = document.getElementById('strategy-signal');
            if (data.strategy.signal) {
                elSignal.style.display = 'block';
                elSignal.innerText = data.strategy.signal.text;
                elSignal.style.color = data.strategy.signal.color;
                elSignal.style.borderColor = data.strategy.signal.color;

                // Trigger visual alert
                showTradeAlert(data.strategy.signal.text, data.ticker);

                // Regime
                if (data.strategy.signal.regime) {
                    document.getElementById('val-regime').innerText = data.strategy.signal.regime;
                    document.getElementById('val-regime-note').innerText = data.strategy.signal.note;
                }
            } else {
                elSignal.style.display = 'none';
            }

            document.getElementById('strategy-name').innerText = data.strategy.name;
            document.getElementById('strategy-rationale').innerText = data.strategy.rationale;
            document.getElementById('strategy-legs').innerHTML = data.strategy.legs.join('<br>');

            // New Stats
            document.getElementById('strategy-premium').innerText = '$' + (data.strategy.premium || 0).toFixed(2);
            document.getElementById('strategy-pop').innerText = (data.strategy.pop || 0) + '%';

            const sName = document.getElementById('strategy-name');
            if (data.strategy.name.includes('Bull')) sName.style.color = '#00ff9d';
            else if (data.strategy.name.includes('Bear')) sName.style.color = '#ff3366';
            else sName.style.color = '#e0e0e0';
        }
        if (data.call_wall) document.getElementById('val-call-wall').innerText = data.call_wall;
        if (data.put_wall) document.getElementById('val-put-wall').innerText = data.put_wall;
        if (data.max_oi) document.getElementById('val-max-oi').innerText = data.max_oi;

        // Market Stats
        if (data.zero_dte_iv) document.getElementById('val-iv').innerText = data.zero_dte_iv + '%';
        if (data.expected_move) document.getElementById('val-move').innerText = '±$' + data.expected_move;

        // P/C Ratio with sentiment coloring
        if (data.put_call_ratio) {
            const pcEl = document.getElementById('val-pc-ratio');
            const ratio = data.put_call_ratio;

            // > 1 = Bearish (more puts), < 1 = Bullish (more calls)
            let sentiment = '';
            let color = '';
            if (ratio > 1.2) {
                sentiment = ' (Bearish)';
                color = '#ff3366';
            } else if (ratio < 0.8) {
                sentiment = ' (Bullish)';
                color = '#00ff9d';
            } else {
                sentiment = ' (Neutral)';
                color = '#ffcc00';
            }

            pcEl.innerText = ratio.toFixed(2) + sentiment;
            pcEl.style.color = color;
        }

        // AI Analysis
        if (data.ai_analysis) {
            const ai = data.ai_analysis;
            document.getElementById('ai-pin').innerText = ai.pin_recommendation || '--';
            document.getElementById('ai-trade').innerText = ai.trade_setup || '--';
            document.getElementById('ai-probability').innerText = ai.probability ? ai.probability + '%' : '--%';
            document.getElementById('ai-rr').innerText = ai.risk_reward || '--';
            document.getElementById('ai-context').innerText = ai.context || '--';
        }

        // Chart Data (Bar)
        // Chart Data (Bar)
        const colors = data.gex.map((val, i) => {
            const strike = data.strikes[i];
            if (strike === data.call_wall) return '#00ffff'; // Cyan for Call Wall
            if (strike === data.put_wall) return '#ff00ff'; // Magenta for Put Wall
            return val >= 0 ? '#00ff9d' : '#ff3366';
        });
        gexChart.data.labels = data.strikes;
        gexChart.data.datasets[0].data = data.gex;
        gexChart.data.datasets[0].backgroundColor = colors;

        // Update OI/Vol
        // Update Custom Data for Tooltip
        gexChart.data.customData = {
            oi: data.oi || [],
            volume: data.volume || []
        };

        // Removed OI/Vol datasets update

        // Spot Line (Dataset Method)
        if (data.strikes.length > 0) {
            const closestStrike = data.strikes.reduce((prev, curr) => Math.abs(curr - data.price) < Math.abs(prev - data.price) ? curr : prev);
            const minY = Math.min(...data.gex);
            const maxY = Math.max(...data.gex);

            gexChart.data.datasets[1].data = [
                { x: closestStrike, y: minY * 1.1 },
                { x: closestStrike, y: maxY * 1.1 }
            ];

            // Annotations (Walls/MaxOI Only)
            const annotations = {};
            if (data.call_wall) {
                annotations.callWall = {
                    type: 'line',
                    scaleID: 'x',
                    value: data.call_wall,
                    borderColor: 'rgba(0, 255, 157, 0.4)',
                    borderWidth: 2,
                    label: { display: true, content: 'CALL WALL', color: '#00ff9d', position: 'end', rotation: 90, backgroundColor: 'rgba(0,0,0,0.8)' }
                };
            }
            if (data.put_wall) {
                annotations.putWall = {
                    type: 'line',
                    scaleID: 'x',
                    value: data.put_wall,
                    borderColor: 'rgba(255, 51, 102, 0.4)',
                    borderWidth: 2,
                    label: { display: true, content: 'PUT WALL', color: '#ff3366', position: 'end', rotation: 90, backgroundColor: 'rgba(0,0,0,0.8)' }
                };
            }
            if (data.max_oi) {
                annotations.maxOI = {
                    type: 'line',
                    scaleID: 'x',
                    value: data.max_oi,
                    borderColor: '#bf00ff',
                    borderWidth: 2,
                    borderDash: [2, 4],
                    label: { display: true, content: 'MAX OI', color: '#bf00ff', position: 'center', rotation: 90, backgroundColor: 'rgba(0,0,0,0.8)' }
                };
            }
            gexChart.options.plugins.annotation.annotations = annotations;
            gexChart.update();

            // HTML Flag Positioning (Post-Update)
            setTimeout(() => {
                const closestIndex = data.strikes.indexOf(closestStrike);
                const xPixel = gexChart.scales.x.getPixelForValue(closestIndex);

                // console.log("Flag Pos - Strike:", closestStrike, "Index:", closestIndex, "X:", xPixel);

                const flag = document.getElementById('spot-flag');
                if (xPixel !== undefined && !isNaN(xPixel)) {
                    flag.style.display = 'block';
                    flag.style.left = xPixel + 'px';
                    flag.innerText = 'SPOT: ' + data.price.toFixed(2);
                } else {
                    // console.warn("Flag Position Invalid");
                    flag.style.display = 'none';
                }
            }, 100);
        }
    }

    // Initialize
    // Set Default to Today
    const today = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD
    elExpiryDate.value = today;

    initChart();
    fetchData();
    setupAutoRefresh(); // Start loop based on dropdown default
});

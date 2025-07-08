// Drug Shortage Prediction Dashboard JavaScript
// Main application logic with D3.js visualizations

let currentPredictions = [];
let summaryData = {};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

// Main function to load all dashboard components
async function loadDashboard() {
    try {
        // Load summary data first
        await loadSummaryData();
        
        // Load and display all charts
        await Promise.all([
            loadModelPerformance(),
            loadFeatureImportance(),
            loadRiskDistribution(),
            loadShortageTimeline(),
            loadCompanyRisk(),
            loadCategoryAnalysis(),
            loadPredictions()
        ]);
        
        // Hide loading, show content
        document.getElementById('loading').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data. Please check your connection and try again.');
    }
}

// Load summary statistics
async function loadSummaryData() {
    try {
        const response = await fetch('/api/summary');
        summaryData = await response.json();
        
        // Update summary cards
        document.getElementById('total-shortages').textContent = 
            summaryData.shortage_data.total_records.toLocaleString();
        document.getElementById('total-enforcements').textContent = 
            summaryData.enforcement_data.total_records.toLocaleString();
        
        // Get high risk count from predictions
        const predictionsResponse = await fetch('/api/predictions?limit=1000');
        const predictionsData = await predictionsResponse.json();
        const highRiskCount = predictionsData.predictions.filter(p => p.risk_level === 'High').length;
        document.getElementById('high-risk-count').textContent = highRiskCount.toLocaleString();
        
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

// Load model performance chart
async function loadModelPerformance() {
    try {
        const response = await fetch('/api/model_performance');
        const data = await response.json();
        
        // Update model accuracy in summary
        const models = Object.keys(data);
        const bestScore = Math.max(...models.map(m => data[m].auc_score));
        document.getElementById('model-accuracy').textContent = (bestScore * 100).toFixed(1) + '%';
        
        // Create bar chart for model performance
        createModelPerformanceChart(data);
        
    } catch (error) {
        console.error('Error loading model performance:', error);
    }
}

// Create model performance bar chart
function createModelPerformanceChart(data) {
    const container = d3.select('#model-performance-chart');
    container.selectAll('*').remove();
    
    const margin = {top: 20, right: 30, bottom: 60, left: 60};
    const width = 350 - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Prepare data
    const chartData = Object.entries(data).map(([model, metrics]) => ({
        model: model.replace('_', ' ').toUpperCase(),
        auc_score: metrics.auc_score
    }));
    
    // Scales
    const xScale = d3.scaleBand()
        .domain(chartData.map(d => d.model))
        .range([0, width])
        .padding(0.1);
    
    const yScale = d3.scaleLinear()
        .domain([0, 1])
        .range([height, 0]);
    
    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain(chartData.map(d => d.model))
        .range(['#4a90e2', '#7b68ee', '#20b2aa']);
    
    // Create bars
    g.selectAll('.bar')
        .data(chartData)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', d => xScale(d.model))
        .attr('width', xScale.bandwidth())
        .attr('y', d => yScale(d.auc_score))
        .attr('height', d => height - yScale(d.auc_score))
        .attr('fill', d => colorScale(d.model))
        .on('mouseover', function(event, d) {
            showTooltip(event, `${d.model}: ${(d.auc_score * 100).toFixed(1)}%`);
        })
        .on('mouseout', hideTooltip);
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)');
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale).tickFormat(d3.format('.0%')));
    
    // Add value labels on bars
    g.selectAll('.value-label')
        .data(chartData)
        .enter().append('text')
        .attr('class', 'value-label')
        .attr('x', d => xScale(d.model) + xScale.bandwidth() / 2)
        .attr('y', d => yScale(d.auc_score) - 5)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', '#333')
        .text(d => (d.auc_score * 100).toFixed(1) + '%');
}

// Load feature importance chart
async function loadFeatureImportance() {
    try {
        const response = await fetch('/api/feature_importance');
        const data = await response.json();
        createFeatureImportanceChart(data);
    } catch (error) {
        console.error('Error loading feature importance:', error);
    }
}

// Create feature importance horizontal bar chart
function createFeatureImportanceChart(data) {
    const container = d3.select('#feature-importance-chart');
    container.selectAll('*').remove();
    
    const margin = {top: 20, right: 30, bottom: 40, left: 180};
    const width = 400 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Take top 10 features
    const chartData = data.slice(0, 10);
    
    // Scales
    const xScale = d3.scaleLinear()
        .domain([0, d3.max(chartData, d => d.importance)])
        .range([0, width]);
    
    const yScale = d3.scaleBand()
        .domain(chartData.map(d => d.feature))
        .range([0, height])
        .padding(0.1);
    
    // Create bars
    g.selectAll('.bar')
        .data(chartData)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', 0)
        .attr('y', d => yScale(d.feature))
        .attr('width', d => xScale(d.importance))
        .attr('height', yScale.bandwidth())
        .attr('fill', '#4a90e2')
        .on('mouseover', function(event, d) {
            showTooltip(event, `${d.feature}: ${d.importance.toFixed(4)}`);
        })
        .on('mouseout', hideTooltip);
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale));
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale))
        .selectAll('text')
        .style('font-size', '10px');
}

// Load risk distribution chart
async function loadRiskDistribution() {
    try {
        const response = await fetch('/api/risk_distribution');
        const data = await response.json();
        createRiskDistributionChart(data);
    } catch (error) {
        console.error('Error loading risk distribution:', error);
    }
}

// Create risk distribution pie chart
function createRiskDistributionChart(data) {
    const container = d3.select('#risk-distribution-chart');
    container.selectAll('*').remove();
    
    const width = 350;
    const height = 250;
    const radius = Math.min(width, height) / 2 - 20;
    
    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);
    
    const g = svg.append('g')
        .attr('transform', `translate(${width / 2},${height / 2})`);
    
    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain(['High', 'Medium', 'Low'])
        .range(['#ff6b6b', '#ffa726', '#66bb6a']);
    
    // Create pie layout
    const pie = d3.pie()
        .value(d => d.count)
        .sort(null);
    
    const arc = d3.arc()
        .innerRadius(0)
        .outerRadius(radius);
    
    const arcs = g.selectAll('.arc')
        .data(pie(data))
        .enter().append('g')
        .attr('class', 'arc');
    
    arcs.append('path')
        .attr('d', arc)
        .attr('fill', d => colorScale(d.data.risk_level))
        .on('mouseover', function(event, d) {
            showTooltip(event, `${d.data.risk_level}: ${d.data.count} drugs`);
        })
        .on('mouseout', hideTooltip);
    
    // Add labels
    arcs.append('text')
        .attr('transform', d => `translate(${arc.centroid(d)})`)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', 'white')
        .style('font-weight', 'bold')
        .text(d => d.data.count);
    
    // Add legend
    const legend = svg.append('g')
        .attr('transform', `translate(${width - 100}, 20)`);
    
    const legendItems = legend.selectAll('.legend-item')
        .data(data)
        .enter().append('g')
        .attr('class', 'legend-item')
        .attr('transform', (d, i) => `translate(0, ${i * 20})`);
    
    legendItems.append('rect')
        .attr('width', 12)
        .attr('height', 12)
        .attr('fill', d => colorScale(d.risk_level));
    
    legendItems.append('text')
        .attr('x', 16)
        .attr('y', 9)
        .style('font-size', '12px')
        .text(d => d.risk_level);
}

// Load shortage timeline chart
async function loadShortageTimeline() {
    try {
        const response = await fetch('/api/shortage_timeline');
        const data = await response.json();
        createTimelineChart(data, '#shortage-timeline-chart');
    } catch (error) {
        console.error('Error loading shortage timeline:', error);
    }
}

// Create timeline chart
function createTimelineChart(data, containerId) {
    const container = d3.select(containerId);
    container.selectAll('*').remove();
    
    const margin = {top: 20, right: 30, bottom: 60, left: 60};
    const width = 400 - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Parse dates
    const parseDate = d3.timeParse('%Y-%m');
    data.forEach(d => {
        d.date = parseDate(d.month);
        d.count = +d.count;
    });
    
    // Sort by date
    data.sort((a, b) => a.date - b.date);
    
    // Scales
    const xScale = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, width]);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.count)])
        .range([height, 0]);
    
    // Create line
    const line = d3.line()
        .x(d => xScale(d.date))
        .y(d => yScale(d.count))
        .curve(d3.curveMonotoneX);
    
    g.append('path')
        .datum(data)
        .attr('class', 'line')
        .attr('d', line);
    
    // Add dots
    g.selectAll('.dot')
        .data(data)
        .enter().append('circle')
        .attr('class', 'dot')
        .attr('cx', d => xScale(d.date))
        .attr('cy', d => yScale(d.count))
        .attr('r', 3)
        .on('mouseover', function(event, d) {
            showTooltip(event, `${d.month}: ${d.count} shortages`);
        })
        .on('mouseout', hideTooltip);
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%Y-%m')))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)');
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale));
}

// Load company risk chart
async function loadCompanyRisk() {
    try {
        const response = await fetch('/api/company_risk');
        const data = await response.json();
        createCompanyRiskChart(data);
    } catch (error) {
        console.error('Error loading company risk:', error);
    }
}

// Create company risk chart
function createCompanyRiskChart(data) {
    const container = d3.select('#company-risk-chart');
    container.selectAll('*').remove();
    
    const margin = {top: 20, right: 30, bottom: 60, left: 120};
    const width = 400 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Take top 10 companies
    const chartData = data.slice(0, 10);
    
    // Scales
    const xScale = d3.scaleLinear()
        .domain([0, d3.max(chartData, d => d.risk_score)])
        .range([0, width]);
    
    const yScale = d3.scaleBand()
        .domain(chartData.map(d => d.company))
        .range([0, height])
        .padding(0.1);
    
    // Create bars
    g.selectAll('.bar')
        .data(chartData)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', 0)
        .attr('y', d => yScale(d.company))
        .attr('width', d => xScale(d.risk_score))
        .attr('height', yScale.bandwidth())
        .attr('fill', '#ff6b6b')
        .on('mouseover', function(event, d) {
            showTooltip(event, `${d.company}<br/>Shortages: ${d.shortages}<br/>Enforcements: ${d.enforcements}<br/>Risk Score: ${d.risk_score.toFixed(1)}`);
        })
        .on('mouseout', hideTooltip);
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale));
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale))
        .selectAll('text')
        .style('font-size', '10px');
}

// Load category analysis chart
async function loadCategoryAnalysis() {
    try {
        const response = await fetch('/api/drug_categories');
        const data = await response.json();
        createCategoryChart(data);
    } catch (error) {
        console.error('Error loading category analysis:', error);
    }
}

// Create category chart
function createCategoryChart(data) {
    const container = d3.select('#category-analysis-chart');
    container.selectAll('*').remove();
    
    const margin = {top: 20, right: 30, bottom: 80, left: 60};
    const width = 400 - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Scales
    const xScale = d3.scaleBand()
        .domain(data.map(d => d.category))
        .range([0, width])
        .padding(0.1);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.count)])
        .range([height, 0]);
    
    // Create bars
    g.selectAll('.bar')
        .data(data)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', d => xScale(d.category))
        .attr('width', xScale.bandwidth())
        .attr('y', d => yScale(d.count))
        .attr('height', d => height - yScale(d.count))
        .attr('fill', '#20b2aa')
        .on('mouseover', function(event, d) {
            showTooltip(event, `${d.category}: ${d.count} shortages`);
        })
        .on('mouseout', hideTooltip);
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)')
        .style('font-size', '10px');
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale));
}

// Load predictions and create table
async function loadPredictions() {
    try {
        const response = await fetch('/api/predictions?limit=50');
        const data = await response.json();
        currentPredictions = data.predictions;
        createPredictionsTable(currentPredictions);
    } catch (error) {
        console.error('Error loading predictions:', error);
    }
}

// Create predictions table
function createPredictionsTable(predictions) {
    const container = d3.select('#predictions-table');
    container.selectAll('*').remove();
    
    const table = container.append('table')
        .attr('class', 'predictions-table');
    
    // Header
    const thead = table.append('thead');
    thead.append('tr')
        .selectAll('th')
        .data(['Drug Name', 'Company', 'Risk Level', 'Probability', 'Action'])
        .enter().append('th')
        .text(d => d);
    
    // Body
    const tbody = table.append('tbody');
    const rows = tbody.selectAll('tr')
        .data(predictions)
        .enter().append('tr');
    
    rows.append('td')
        .text(d => d.drug_name);
    
    rows.append('td')
        .text(d => d.company_name);
    
    rows.append('td')
        .html(d => `<span class="risk-${d.risk_level.toLowerCase()}">${d.risk_level}</span>`);
    
    rows.append('td')
        .text(d => (d.shortage_probability * 100).toFixed(1) + '%');
    
    rows.append('td')
        .html(d => d.shortage_probability > 0.7 ? 
            '<span style="color: #ff6b6b;">⚠️ Monitor Closely</span>' : 
            '<span style="color: #66bb6a;">✅ Normal</span>');
}

// Update predictions based on filters
async function updatePredictions() {
    const riskLevel = document.getElementById('risk-filter').value;
    const company = document.getElementById('company-filter').value;
    
    let url = '/api/predictions?limit=50';
    if (riskLevel) url += `&risk_level=${riskLevel}`;
    if (company) url += `&company=${encodeURIComponent(company)}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        createPredictionsTable(data.predictions);
    } catch (error) {
        console.error('Error updating predictions:', error);
    }
}

// Search for specific drug
async function searchDrug() {
    const drugName = document.getElementById('drug-search').value;
    if (!drugName) return;
    
    try {
        const response = await fetch(`/api/search_drug?drug_name=${encodeURIComponent(drugName)}`);
        const data = await response.json();
        
        const resultsContainer = document.getElementById('drug-search-results');
        const resultsContent = document.getElementById('search-results-content');
        
        if (data.length > 0) {
            resultsContent.innerHTML = `
                <div class="search-result">
                    <h4>${data[0].drug_name}</h4>
                    <p><strong>Company:</strong> ${data[0].company_name}</p>
                    <p><strong>Risk Level:</strong> <span class="risk-${data[0].risk_level.toLowerCase()}">${data[0].risk_level}</span></p>
                    <p><strong>Shortage Probability:</strong> ${(data[0].shortage_probability * 100).toFixed(1)}%</p>
                </div>
            `;
        } else {
            resultsContent.innerHTML = '<p>No predictions found for this drug.</p>';
        }
        
        resultsContainer.style.display = 'block';
    } catch (error) {
        console.error('Error searching drug:', error);
    }
}

// Utility functions
function showTooltip(event, text) {
    const tooltip = d3.select('body').append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0);
    
    tooltip.html(text)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px')
        .transition()
        .duration(200)
        .style('opacity', 1);
}

function hideTooltip() {
    d3.selectAll('.tooltip').remove();
}

function showError(message) {
    const loading = document.getElementById('loading');
    loading.innerHTML = `
        <div style="color: #ff6b6b; font-size: 1.2em;">
            ❌ ${message}
        </div>
    `;
} 
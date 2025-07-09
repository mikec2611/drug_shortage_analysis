// ===== GLOBAL VARIABLES =====
let globalData = {};
let selectedCompany = null;

// Color schemes
const colorSchemes = {
    primary: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'],
    categorical: ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
    severity: {
        'Class I': '#ef4444',
        'Class II': '#f59e0b',
        'Class III': '#10b981',
        'Class IV': '#6b7280'
    }
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    setupEventListeners();
    loadCompanies();
    loadDashboardData();
}

function setupEventListeners() {
    // Company filter change
    const companySelect = document.getElementById('companySelect');
    if (companySelect) {
        companySelect.addEventListener('change', function() {
            selectedCompany = this.value || null;
            console.log('Selected company:', selectedCompany);
            loadDashboardData();
        });
    }
    
    // Chart controls
    const companyLimit = document.getElementById('companyLimit');
    if (companyLimit) {
        companyLimit.addEventListener('change', function() {
            if (globalData.companyAnalysis) {
                loadCompanyAnalysis();
            }
        });
    }
    
    const drugsLimit = document.getElementById('drugsLimit');
    if (drugsLimit) {
        drugsLimit.addEventListener('change', function() {
            if (globalData.topDrugs) {
                loadTopDrugs();
            }
        });
    }
    
    const activityType = document.getElementById('activityType');
    if (activityType) {
        activityType.addEventListener('change', function() {
            if (globalData.recentActivity) {
                loadRecentActivity();
            }
        });
    }
    
    // Window resize handler
    window.addEventListener('resize', debounce(function() {
        if (globalData.monthlyTrends) {
            createMonthlyTrendsChart(globalData.monthlyTrends);
            createCompanyAnalysisChart(globalData.companyAnalysis);
            createTherapeuticCategoriesChart(globalData.therapeuticCategories);
            createGeographicChart(globalData.geographicAnalysis);
            createShortageReasonsChart(globalData.shortageReasons);
            createRecallSeverityChart(globalData.recallSeverity);
            createTopDrugsChart(globalData.topDrugs);
        }
    }, 250));
}

// ===== UTILITY FUNCTIONS =====
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function getContainerDimensions(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return { width: 400, height: 300 };
    
    const rect = container.getBoundingClientRect();
    const computedStyle = window.getComputedStyle(container);
    
    // Get dimensions with fallbacks and minimum values
    const width = Math.max(300, rect.width || parseInt(computedStyle.width) || 400);
    const height = Math.max(250, rect.height || parseInt(computedStyle.height) || 300);
    
    return { width, height };
}

function formatNumber(num) {
    return num.toLocaleString();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('dashboard-content').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('dashboard-content').style.display = 'block';
    document.getElementById('dashboard-content').classList.add('fade-in');
}

function showError() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('dashboard-content').style.display = 'none';
    document.getElementById('error-message').style.display = 'block';
}

// ===== API FUNCTIONS =====
async function fetchData(endpoint) {
    try {
        const params = new URLSearchParams();
        if (selectedCompany) {
            params.append('company', selectedCompany);
        }
        
        const url = `/api/${endpoint}${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
}

async function loadDashboardData() {
    try {
        showLoading();
        
        // Load all data in parallel
        const [
            summaryMetrics,
            monthlyTrends,
            companyAnalysis,
            therapeuticCategories,
            geographicAnalysis,
            topDrugs,
            shortageReasons,
            recallSeverity,
            recentActivity
        ] = await Promise.all([
            selectedCompany ? fetchData('summary_metrics') : fetchData('summary_metrics'),
            fetchData('monthly_trends'),
            fetchData('company_analysis'),
            fetchData('therapeutic_categories'),
            selectedCompany ? fetchData('geographic_analysis') : fetchData('geographic_analysis'),
            fetchData('top_drugs'),
            selectedCompany ? fetchData('shortage_reasons') : fetchData('shortage_reasons'),
            selectedCompany ? fetchData('recall_severity') : fetchData('recall_severity'),
            fetchData('recent_activity')
        ]);

        // Store data globally
        globalData = {
            summaryMetrics,
            monthlyTrends,
            companyAnalysis,
            therapeuticCategories,
            geographicAnalysis,
            topDrugs,
            shortageReasons,
            recallSeverity,
            recentActivity
        };

        // Update dashboard - only update summary metrics if no company is selected
        if (!selectedCompany) {
            updateSummaryMetrics(summaryMetrics);
        }
        
        // Hide loading and show content first
        hideLoading();
        
        // Wait a bit for layout to settle, then create charts
        await new Promise(resolve => setTimeout(resolve, 100));
        
        createMonthlyTrendsChart(monthlyTrends);
        createCompanyAnalysisChart(companyAnalysis);
        createTherapeuticCategoriesChart(therapeuticCategories);
        createGeographicChart(geographicAnalysis);
        createShortageReasonsChart(shortageReasons);
        createRecallSeverityChart(recallSeverity);
        createTopDrugsChart(topDrugs);
        createTopDrugsTable(topDrugs);
        createRecentActivityTable(recentActivity);

        console.log('Dashboard loaded successfully!', selectedCompany ? `(filtered by: ${selectedCompany})` : '(all data)');
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError();
    }
}

// ===== LOAD COMPANIES FOR DROPDOWN =====
async function loadCompanies() {
    try {
        const response = await fetch('/api/companies');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const companies = await response.json();
        console.log('Companies API response:', companies);
        
        const select = document.getElementById('companySelect');
        if (!select) {
            console.warn('Company select element not found');
            return;
        }
        
        // Check if response is an error object
        if (companies.error) {
            console.error('API returned error:', companies.error);
            return;
        }
        
        // Check if companies is actually an array
        if (!Array.isArray(companies)) {
            console.error('Companies response is not an array:', companies);
            return;
        }
        
        // Clear existing options (keep "All Companies")
        select.innerHTML = '<option value="">All Companies</option>';
        
        // Add company options
        companies.forEach(company => {
            const option = document.createElement('option');
            option.value = company;
            option.textContent = company;
            select.appendChild(option);
        });
        
        console.log('Successfully loaded', companies.length, 'companies');
    } catch (error) {
        console.error('Error loading companies:', error);
        
        // Show a user-friendly message
        const select = document.getElementById('companySelect');
        if (select) {
            select.innerHTML = '<option value="">All Companies (Error loading list)</option>';
        }
    }
}

// ===== SUMMARY METRICS =====
function updateSummaryMetrics(data) {
    // Debug: Log the data to see what we're working with
    console.log('Summary metrics data:', data);
    
    // Update metrics cards using the correct HTML IDs
    document.getElementById('totalIssues').textContent = 
        data.total_issues?.toLocaleString() || '0';
    document.getElementById('companiesAffected').textContent = 
        data.total_companies_affected?.toLocaleString() || '0';
    document.getElementById('currentShortages').textContent = 
        data.active_shortages?.toLocaleString() || '0';
    document.getElementById('classIRecalls').textContent = 
        data.class_i_recalls?.toLocaleString() || '0';
    document.getElementById('ongoingRecalls').textContent = 
        data.ongoing_recalls?.toLocaleString() || '0';
    document.getElementById('recentActivity').textContent = 
        (data.shortages_last_30_days + data.enforcements_last_30_days)?.toLocaleString() || '0';
    
    // Add debug info in console
    console.log('Current shortages (strict):', data.current_shortages);
    console.log('Active shortages (inclusive):', data.active_shortages);
    console.log('Total companies affected:', data.total_companies_affected);
    console.log('Showing active shortages in UI');
}

// ===== MONTHLY TRENDS CHART =====
function createMonthlyTrendsChart(data) {
    const container = d3.select('#monthlyTrendsChart');
    container.selectAll('*').remove();
    
    if (!data || data.length === 0) {
        container.append('div')
            .attr('class', 'no-data')
            .style('text-align', 'center')
            .style('padding', '2rem')
            .style('color', '#6b7280')
            .text('No data available');
        return;
    }
    
    const dimensions = getContainerDimensions('monthlyTrendsChart');
    const margin = {top: 20, right: 80, bottom: 60, left: 80};
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Parse dates
    data.forEach(d => {
        d.month = new Date(d.month);
    });
    
    // Scales
    const xScale = d3.scaleTime()
        .domain(d3.extent(data, d => d.month))
        .range([0, width]);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => Math.max(d.shortage_count, d.enforcement_count))])
        .range([height, 0]);
    
    // Line generators
    const shortageLine = d3.line()
        .x(d => xScale(d.month))
        .y(d => yScale(d.shortage_count))
        .curve(d3.curveMonotoneX);
    
    const enforcementLine = d3.line()
        .x(d => xScale(d.month))
        .y(d => yScale(d.enforcement_count))
        .curve(d3.curveMonotoneX);
    
    // Add grid
    g.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale).tickSize(-height).tickFormat(''));
    
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(''));
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%b %Y')));
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale));
    
    // Add lines
    g.append('path')
        .datum(data)
        .attr('class', 'line')
        .attr('stroke', colorSchemes.primary[0])
        .attr('d', shortageLine);
    
    g.append('path')
        .datum(data)
        .attr('class', 'line')
        .attr('stroke', colorSchemes.primary[1])
        .attr('d', enforcementLine);
    
    // Add dots
    g.selectAll('.dot-shortage')
        .data(data)
        .enter().append('circle')
        .attr('class', 'dot')
        .attr('cx', d => xScale(d.month))
        .attr('cy', d => yScale(d.shortage_count))
        .attr('r', 4)
        .attr('stroke', colorSchemes.primary[0])
        .on('mouseover', function(event, d) {
            showTooltip(event, `Shortages: ${d.shortage_count}<br>Month: ${d3.timeFormat('%b %Y')(d.month)}`);
        })
        .on('mouseout', hideTooltip);
    
    g.selectAll('.dot-enforcement')
        .data(data)
        .enter().append('circle')
        .attr('class', 'dot')
        .attr('cx', d => xScale(d.month))
        .attr('cy', d => yScale(d.enforcement_count))
        .attr('r', 4)
        .attr('stroke', colorSchemes.primary[1])
        .on('mouseover', function(event, d) {
            showTooltip(event, `Enforcements: ${d.enforcement_count}<br>Month: ${d3.timeFormat('%b %Y')(d.month)}`);
        })
        .on('mouseout', hideTooltip);
    
    // Add legend
    const legend = g.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${width - 100}, 20)`);
    
    legend.append('line')
        .attr('x1', 0).attr('x2', 15)
        .attr('y1', 0).attr('y2', 0)
        .attr('stroke', colorSchemes.primary[0])
        .attr('stroke-width', 2);
    
    legend.append('text')
        .attr('x', 20).attr('y', 0)
        .attr('dy', '0.35em')
        .text('Shortages');
    
    legend.append('line')
        .attr('x1', 0).attr('x2', 15)
        .attr('y1', 20).attr('y2', 20)
        .attr('stroke', colorSchemes.primary[1])
        .attr('stroke-width', 2);
    
    legend.append('text')
        .attr('x', 20).attr('y', 20)
        .attr('dy', '0.35em')
        .text('Enforcements');
}

// ===== COMPANY ANALYSIS CHART =====
function createCompanyAnalysisChart(data) {
    const container = d3.select('#companyAnalysisChart');
    container.selectAll('*').remove();
    
    if (!data || data.length === 0) {
        container.append('div')
            .attr('class', 'no-data')
            .style('text-align', 'center')
            .style('padding', '2rem')
            .style('color', '#6b7280')
            .text('No data available');
        return;
    }
    
    const dimensions = getContainerDimensions('companyAnalysisChart');
    const margin = {top: 20, right: 20, bottom: 120, left: 60};
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Scales
    const xScale = d3.scaleBand()
        .domain(data.map(d => d.company_name))
        .range([0, width])
        .padding(0.1);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.total_issues)])
        .range([height, 0]);
    
    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain(['Shortage Only', 'Enforcement Only', 'Both Issues'])
        .range(colorSchemes.categorical);
    
    // Add grid
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(''));
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-0.8em')
        .attr('dy', '0.15em')
        .attr('transform', 'rotate(-45)');
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale));
    
    // Add bars
    g.selectAll('.bar')
        .data(data)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', d => xScale(d.company_name))
        .attr('width', xScale.bandwidth())
        .attr('y', d => yScale(d.total_issues))
        .attr('height', d => height - yScale(d.total_issues))
        .attr('fill', d => colorScale(d.issue_type))
        .on('mouseover', function(event, d) {
            showTooltip(event, `
                <strong>${d.company_name}</strong><br>
                Total Issues: ${d.total_issues}<br>
                Shortages: ${d.shortage_count}<br>
                Enforcements: ${d.enforcement_count}<br>
                Class I Recalls: ${d.class_i_recalls}
            `);
        })
        .on('mouseout', hideTooltip)
        .on('click', function(event, d) {
            // Navigate to company detail page
            window.location.href = `/company/${encodeURIComponent(d.company_name)}`;
        });
}

// ===== THERAPEUTIC CATEGORIES CHART =====
function createTherapeuticCategoriesChart(data) {
    const container = d3.select('#therapeuticCategoriesChart');
    container.selectAll('*').remove();
    
    if (!data || data.length === 0) {
        container.append('div')
            .attr('class', 'no-data')
            .style('text-align', 'center')
            .style('padding', '2rem')
            .style('color', '#6b7280')
            .text('No data available');
        return;
    }
    
    const dimensions = getContainerDimensions('therapeuticCategoriesChart');
    const width = dimensions.width;
    const height = dimensions.height;
    const radius = Math.min(width, height) / 2 - 20;
    
    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);
    
    const g = svg.append('g')
        .attr('transform', `translate(${width/2},${height/2})`);
    
    // Take top 10 categories
    const topData = data.slice(0, 10);
    
    const pie = d3.pie()
        .value(d => d.shortage_count)
        .sort(null);
    
    const arc = d3.arc()
        .innerRadius(0)
        .outerRadius(radius);
    
    const labelArc = d3.arc()
        .innerRadius(radius * 0.6)
        .outerRadius(radius * 0.6);
    
    const color = d3.scaleOrdinal()
        .domain(topData.map(d => d.therapeutic_category))
        .range(colorSchemes.primary);
    
    const arcs = g.selectAll('.arc')
        .data(pie(topData))
        .enter().append('g')
        .attr('class', 'arc');
    
    arcs.append('path')
        .attr('d', arc)
        .attr('fill', d => color(d.data.therapeutic_category))
        .on('mouseover', function(event, d) {
            showTooltip(event, `
                <strong>${d.data.therapeutic_category}</strong><br>
                Shortages: ${d.data.shortage_count}<br>
                Companies: ${d.data.companies_affected}<br>
                Drugs: ${d.data.drugs_affected}
            `);
        })
        .on('mouseout', hideTooltip);
    
    arcs.append('text')
        .attr('transform', d => `translate(${labelArc.centroid(d)})`)
        .attr('dy', '0.35em')
        .style('text-anchor', 'middle')
        .style('font-size', '10px')
        .text(d => d.data.shortage_count > 10 ? d.data.shortage_count : '');
}

// ===== GEOGRAPHIC CHART =====
function createGeographicChart(data) {
    const container = d3.select('#geographicChart');
    container.selectAll('*').remove();
    
    if (!data || data.length === 0) {
        container.append('div')
            .attr('class', 'no-data')
            .style('text-align', 'center')
            .style('padding', '2rem')
            .style('color', '#6b7280')
            .text('No data available');
        return;
    }
    
    const dimensions = getContainerDimensions('geographicChart');
    const margin = {top: 20, right: 20, bottom: 80, left: 60};
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Take top 15 states
    const topData = data.slice(0, 15);
    
    const xScale = d3.scaleBand()
        .domain(topData.map(d => d.state))
        .range([0, width])
        .padding(0.1);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(topData, d => d.enforcement_count)])
        .range([height, 0]);
    
    // Add grid
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(''));
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-0.8em')
        .attr('dy', '0.15em')
        .attr('transform', 'rotate(-45)');
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale));
    
    // Add bars
    g.selectAll('.bar')
        .data(topData)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', d => xScale(d.state))
        .attr('width', xScale.bandwidth())
        .attr('y', d => yScale(d.enforcement_count))
        .attr('height', d => height - yScale(d.enforcement_count))
        .attr('fill', colorSchemes.primary[2])
        .on('mouseover', function(event, d) {
            showTooltip(event, `
                <strong>${d.state}</strong><br>
                Enforcements: ${d.enforcement_count}<br>
                Companies: ${d.companies_affected}<br>
                Class I: ${d.class_i_recalls}<br>
                Ongoing: ${d.ongoing_recalls}
            `);
        })
        .on('mouseout', hideTooltip);
}

// ===== SHORTAGE REASONS CHART =====
function createShortageReasonsChart(data) {
    const container = d3.select('#shortageReasonsChart');
    container.selectAll('*').remove();
    
    if (!data || data.length === 0) {
        container.append('div')
            .attr('class', 'no-data')
            .style('text-align', 'center')
            .style('padding', '2rem')
            .style('color', '#6b7280')
            .text('No data available');
        return;
    }
    
    const dimensions = getContainerDimensions('shortageReasonsChart');
    const margin = {top: 20, right: 20, bottom: 100, left: 60};
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const xScale = d3.scaleBand()
        .domain(data.map(d => d.shortage_reason))
        .range([0, width])
        .padding(0.1);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.occurrence_count)])
        .range([height, 0]);
    
    // Add grid
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(''));
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-0.8em')
        .attr('dy', '0.15em')
        .attr('transform', 'rotate(-45)');
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale));
    
    // Add bars
    g.selectAll('.bar')
        .data(data)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', d => xScale(d.shortage_reason))
        .attr('width', xScale.bandwidth())
        .attr('y', d => yScale(d.occurrence_count))
        .attr('height', d => height - yScale(d.occurrence_count))
        .attr('fill', colorSchemes.primary[3])
        .on('mouseover', function(event, d) {
            showTooltip(event, `
                <strong>${d.shortage_reason}</strong><br>
                Occurrences: ${d.occurrence_count}<br>
                Companies: ${d.companies_affected}<br>
                Categories: ${d.categories_affected}<br>
                Current: ${d.current_shortages}
            `);
        })
        .on('mouseout', hideTooltip);
}

// ===== RECALL SEVERITY CHART =====
function createRecallSeverityChart(data) {
    const container = d3.select('#recallSeverityChart');
    container.selectAll('*').remove();
    
    if (!data || data.length === 0) {
        container.append('div')
            .attr('class', 'no-data')
            .style('text-align', 'center')
            .style('padding', '2rem')
            .style('color', '#6b7280')
            .text('No data available');
        return;
    }
    
    const dimensions = getContainerDimensions('recallSeverityChart');
    const width = dimensions.width;
    const height = dimensions.height;
    const radius = Math.min(width, height) / 2 - 20;
    
    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);
    
    const g = svg.append('g')
        .attr('transform', `translate(${width/2},${height/2})`);
    
    const pie = d3.pie()
        .value(d => d.recall_count)
        .sort(null);
    
    const arc = d3.arc()
        .innerRadius(radius * 0.4)
        .outerRadius(radius);
    
    const labelArc = d3.arc()
        .innerRadius(radius * 0.7)
        .outerRadius(radius * 0.7);
    
    const arcs = g.selectAll('.arc')
        .data(pie(data))
        .enter().append('g')
        .attr('class', 'arc');
    
    arcs.append('path')
        .attr('d', arc)
        .attr('fill', d => colorSchemes.severity[d.data.classification] || '#6b7280')
        .on('mouseover', function(event, d) {
            showTooltip(event, `
                <strong>${d.data.classification}</strong><br>
                Recalls: ${d.data.recall_count}<br>
                Companies: ${d.data.companies_affected}<br>
                Ongoing: ${d.data.ongoing_recalls}
            `);
        })
        .on('mouseout', hideTooltip);
    
    arcs.append('text')
        .attr('transform', d => `translate(${labelArc.centroid(d)})`)
        .attr('dy', '0.35em')
        .style('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .text(d => d.data.classification);
}

// ===== TOP DRUGS CHART =====
function createTopDrugsChart(data) {
    const container = d3.select('#topDrugsChart');
    container.selectAll('*').remove();
    
    if (!data || data.length === 0) {
        container.append('div')
            .attr('class', 'no-data')
            .style('text-align', 'center')
            .style('padding', '2rem')
            .style('color', '#6b7280')
            .text('No data available');
        return;
    }
    
    const dimensions = getContainerDimensions('topDrugsChart');
    const margin = {top: 20, right: 40, bottom: 60, left: 150};
    
    // Ensure minimum dimensions to prevent negative values
    const minWidth = 300;
    const minHeight = 250;
    const width = Math.max(minWidth, dimensions.width - margin.left - margin.right);
    const height = Math.max(minHeight, dimensions.height - margin.top - margin.bottom);
    
    // Take top 8 drugs for better readability
    const topData = data.slice(0, 8);
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Scales
    const yScale = d3.scaleBand()
        .domain(topData.map(d => d.generic_name))
        .range([0, height])
        .padding(0.2);
    
    const xScale = d3.scaleLinear()
        .domain([0, d3.max(topData, d => d.shortage_count)])
        .range([0, width]);
    
    // Add grid
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisBottom(xScale).tickSize(height).tickFormat(''));
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale))
        .selectAll('text')
        .style('font-size', '11px')
        .each(function(d) {
            const text = d3.select(this);
            const words = d.split(' ');
            if (words.length > 3) {
                text.text(words.slice(0, 3).join(' ') + '...');
            }
        });
    
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale));
    
    // Add bars with safety check for width
    g.selectAll('.bar')
        .data(topData)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('y', d => yScale(d.generic_name))
        .attr('height', yScale.bandwidth())
        .attr('x', 0)
        .attr('width', d => Math.max(0, xScale(d.shortage_count))) // Ensure non-negative width
        .attr('fill', colorSchemes.primary[4])
        .on('mouseover', function(event, d) {
            showTooltip(event, `
                <strong>${d.generic_name}</strong><br>
                Brand: ${d.proprietary_name || 'N/A'}<br>
                Shortages: ${d.shortage_count}<br>
                Companies: ${d.companies_affected}<br>
                Category: ${d.therapeutic_category}<br>
                Status: ${d.current_status}
            `);
        })
        .on('mouseout', hideTooltip);
    
    // Add value labels on bars
    g.selectAll('.bar-label')
        .data(topData)
        .enter().append('text')
        .attr('class', 'bar-label')
        .attr('x', d => Math.max(5, xScale(d.shortage_count) + 5)) // Ensure label positioning
        .attr('y', d => yScale(d.generic_name) + yScale.bandwidth() / 2)
        .attr('dy', '0.35em')
        .style('font-size', '11px')
        .style('fill', '#374151')
        .text(d => d.shortage_count);
}

// ===== TOP DRUGS TABLE =====
function createTopDrugsTable(data) {
    const container = d3.select('#topDrugsTable');
    container.selectAll('*').remove();
    
    const table = container.append('table');
    const thead = table.append('thead');
    const tbody = table.append('tbody');
    
    const headers = ['Drug Name', 'Brand Name', 'Category', 'Shortages', 'Companies', 'Status'];
    
    thead.append('tr')
        .selectAll('th')
        .data(headers)
        .enter()
        .append('th')
        .text(d => d);
    
    const rows = tbody.selectAll('tr')
        .data(data)
        .enter()
        .append('tr');
    
    rows.selectAll('td')
        .data(d => [
            d.generic_name,
            d.proprietary_name || '-',
            d.therapeutic_category,
            d.shortage_count,
            d.companies_affected,
            d.current_status
        ])
        .enter()
        .append('td')
        .html((d, i) => {
            if (i === 5) { // Status column
                const statusClass = d === 'Currently in shortage' ? 'danger' : 'success';
                return `<span class="badge ${statusClass}">${d}</span>`;
            }
            return d;
        });
}

// ===== RECENT ACTIVITY TABLE =====
function createRecentActivityTable(data) {
    const container = d3.select('#recentActivityTable');
    container.selectAll('*').remove();
    
    const table = container.append('table');
    const thead = table.append('thead');
    const tbody = table.append('tbody');
    
    const headers = ['Type', 'Date', 'Company', 'Drug/Product', 'Status', 'Classification'];
    
    thead.append('tr')
        .selectAll('th')
        .data(headers)
        .enter()
        .append('th')
        .text(d => d);
    
    const rows = tbody.selectAll('tr')
        .data(data)
        .enter()
        .append('tr');
    
    rows.selectAll('td')
        .data(d => [
            d.issue_type,
            formatDate(d.issue_date),
            d.company,
            d.drug_name,
            d.status,
            d.classification
        ])
        .enter()
        .append('td')
        .html((d, i) => {
            if (i === 0) { // Type column
                const typeClass = d === 'Shortage' ? 'warning' : 'primary';
                return `<span class="badge ${typeClass}">${d}</span>`;
            }
            if (i === 5 && d !== 'N/A') { // Classification column
                const classClass = d === 'Class I' ? 'danger' : d === 'Class II' ? 'warning' : 'success';
                return `<span class="badge ${classClass}">${d}</span>`;
            }
            return d;
        });
}

// ===== TOOLTIP FUNCTIONS =====
function showTooltip(event, content) {
    const tooltip = d3.select('body').append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0);
    
    tooltip.html(content)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px')
        .transition()
        .duration(200)
        .style('opacity', 1);
}

function hideTooltip() {
    d3.selectAll('.tooltip').remove();
}

// ===== COMPANY FILTERING =====
// All company filtering functionality is handled in the main loadDashboardData function
// and the company dropdown change event listener

// ===== DYNAMIC LOADING FUNCTIONS =====
async function loadCompanyAnalysis() {
    const limit = document.getElementById('companyLimit').value;
    try {
        const data = await fetchData(`company_analysis?limit=${limit}`);
        createCompanyAnalysisChart(data);
    } catch (error) {
        console.error('Error loading company analysis:', error);
    }
}

async function loadTopDrugs() {
    const limit = document.getElementById('drugsLimit').value;
    try {
        const data = await fetchData(`top_drugs?limit=${limit}`);
        createTopDrugsTable(data);
    } catch (error) {
        console.error('Error loading top drugs:', error);
    }
}

async function loadRecentActivity() {
    const type = document.getElementById('activityType').value;
    const url = type ? `recent_activity?type=${type}` : 'recent_activity';
    try {
        const data = await fetchData(url);
        createRecentActivityTable(data);
    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

// ===== END OF DASHBOARD FUNCTIONS ===== 
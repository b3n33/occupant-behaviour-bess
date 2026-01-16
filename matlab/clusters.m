clear;
close all;

% --- Config ---
ROOT = fileparts(fileparts(mfilename('fullpath')));
if isempty(ROOT)
    ROOT = pwd;
end

DATA_DIR = fullfile(ROOT, 'data');
INPUT_FILE = fullfile(DATA_DIR, 'Absolute_Differences.csv');
OUTPUT_FILE = fullfile(DATA_DIR, 'Cluster_Differences.csv');
FIG_PATH = fullfile(ROOT, 'docs', 'figures', 'clusters_mf.png');

DATA_COLS = 2:5;           
CONFIDENCE_INTERVAL = 0.7; 
NUM_CLUSTERS = 5;          
EXPONENT = 2;              
RNG_SEED = 42;             
PLOT_MF = false;
% --- End config ---

% Reproducibility
if isempty(RNG_SEED)
    rng('shuffle');
    s = rng;
    fprintf('Random seed: %d\n', s.Seed);
else
    rng(RNG_SEED);
    fprintf('Random seed: %d\n', RNG_SEED);
end

% Load and preprocess data
file = readmatrix(INPUT_FILE);
file = fillmissing(file, 'linear');
data_original = file(:, DATA_COLS);
data = data_original(:);

% Clustering
alpha_cut = 1 - CONFIDENCE_INTERVAL;
opt = genfisOptions('FCMClustering');
opt.NumClusters = NUM_CLUSTERS;
opt.Exponent = EXPONENT;

fis = genfis(data, data, opt);

% Membership values for each data point for each cluster
mv = zeros(length(data), opt.NumClusters);
for i = 1:opt.NumClusters
    mfdata(i) = fis.Inputs(1).MembershipFunctions(i);
    mv(:, i) = evalmf(mfdata(i), data);
end

% Upper bounds per cluster based on confidence threshold
x_values = zeros(length(data), opt.NumClusters);
data_rep = repmat(data, 1, opt.NumClusters);
x_values(mv > alpha_cut) = data_rep(mv > alpha_cut);
x_values(x_values == 0) = NaN;
UB = max(x_values, [], 1, 'omitnan');

% Build output matrix
mv = mv';
high_confidence = mv > alpha_cut;
output_matrix = NaN(size(high_confidence));
for row = 1:size(high_confidence, 1)
    output_matrix(row, high_confidence(row, :)) = UB(row);
end

% Final result (sum across buildings)
output_matrix_final = max(output_matrix, [], 1, 'omitnan')';
output_matrix_final_reshaped = reshape(output_matrix_final, size(data_original));
output_matrix_final_reshaped(isnan(output_matrix_final_reshaped)) = 0;
result = sum(output_matrix_final_reshaped, 2);
writematrix(result, OUTPUT_FILE);
fprintf('Wrote: %s\n', OUTPUT_FILE);

% Optional plot of membership functions
if PLOT_MF
    font = 10;
    [x, mf] = plotmf(fis, 'input', 1);
    hold on;
    box on;
    grid on;

    plot(x, mf(:,1), 'LineWidth', 2, 'LineStyle', '-',  'Color', 'blue',    'DisplayName', 'Very Low');
    plot(x, mf(:,2), 'LineWidth', 2, 'LineStyle', '--', 'Color', 'red',     'DisplayName', 'Low');
    plot(x, mf(:,3), 'LineWidth', 2, 'LineStyle', ':',  'Color', 'green',   'DisplayName', 'Medium');
    plot(x, mf(:,4), 'LineWidth', 2, 'LineStyle', '-.', 'Color', 'black',   'DisplayName', 'High');
    plot(x, mf(:,5), 'LineWidth', 2, 'LineStyle', '-',  'Color', 'magenta', 'DisplayName', 'Very High');

    xlabel('Hourly OEB (kWh/m^2)', 'FontSize', font);
    ylabel('Membership Function Degree', 'FontSize', font);

    exportgraphics(gcf, FIG_PATH, 'Resolution', 300);
    fprintf('Saved figure: %s\n', FIG_PATH);
end
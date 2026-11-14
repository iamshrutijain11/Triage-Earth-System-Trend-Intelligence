# TRIAGE: Statistical Climatology & Earth System Trend Analysis Methodology

**NASA Space Apps Challenge 2026: "Be An Earth System Trend Detective!"**

---

## 1. Executive Summary

The **TRIAGE Trend-Analysis Engine** is a mathematically rigorous, reproducible framework designed to transform noisy, seasonal, and irregularly sampled NASA Earth-science observations into defensible statistical findings.

Earth observation records (e.g., precipitation from GPM/IMERG, surface temperature from MODIS/AIRS, soil moisture from SMAP, and snow extent from Landsat/Sentinel) present critical statistical challenges:
- **Seasonality**: Strong annual cycles that obscure long-term trends.
- **Serial Autocorrelation**: Red-noise memory in atmospheric and hydrologic processes that inflates the Type I error rate (false positive trend detection).
- **Non-Normality & Outliers**: Extreme weather events and skewed hydrological distributions that invalidate ordinary least squares (OLS) assumptions.
- **Spatial Multiplicity**: Testing thousands of geographic grid cells simultaneously, which multiplies false positive detections without rigorous multiple-testing control.

TRIAGE implements modern non-parametric climatological statistics to resolve these challenges without fabricating or distorting empirical records.

---

## 2. Mathematical & Statistical Framework

### 2.1 Trend Magnitude: Theil-Sen Median Slope Estimator
Ordinary least-squares (OLS) regression is highly sensitive to outliers (e.g., severe storm anomalies or sensor dropouts). TRIAGE employs the **Theil-Sen estimator** (Theil 1950, Sen 1968), which computes the median of all pairwise slopes across observation timestamps:

$$Q_{ij} = \frac{y_j - y_i}{t_j - t_i} \quad \text{for all } 1 \le i < j \le n$$

$$\beta_{\text{Sen}} = \text{median}(Q_{ij})$$

**Properties**:
- Has a high breakdown point of approximately 29.3%, resisting extreme observational anomalies.
- Units are strictly normalized to climatologically standard time intervals (e.g., `unit / decade`, `unit / year`).

### 2.2 Confidence Interval for Trend Slope
Confidence intervals for $\beta_{\text{Sen}}$ are determined non-parametrically using the rank order distribution of pairwise slopes (Hollander & Wolfe, 1999):

$$C_\alpha = z_{1 - \alpha/2} \sqrt{\frac{n(n - 1)(2n + 5)}{18}}$$

$$M_1 = \frac{N - C_\alpha}{2}, \quad M_2 = \frac{N + C_\alpha}{2}$$

The $(1 - \alpha)$ two-sided confidence interval is $[Q_{(M_1)}, Q_{(M_2)}]$.

---

### 2.3 Trend Significance: Mann-Kendall Test
The Mann-Kendall test (Mann 1945, Kendall 1975) evaluates monotonic trend without assuming a specific data distribution:

$$S = \sum_{i=1}^{n-1} \sum_{j=i+1}^n \text{sgn}(y_j - y_i)$$

$$\text{Var}(S) = \frac{n(n - 1)(2n + 5) - \sum_{p=1}^g t_p(t_p - 1)(2t_p + 5)}{18}$$

Where $t_p$ represents the count of tied observations in tied group $p$. The test statistic $Z$ is computed with continuity correction:

$$Z = \begin{cases} \frac{S - 1}{\sqrt{\text{Var}(S)}} & \text{if } S > 0 \\ 0 & \text{if } S = 0 \\ \frac{S + 1}{\sqrt{\text{Var}(S)}} & \text{if } S < 0 \end{cases}$$

Two-sided $p$-value: $p = 2 \cdot (1 - \Phi(|Z|))$.

---

### 2.4 Seasonal Data: Seasonal Mann-Kendall Test (Hirsch et al., 1982)
> [!IMPORTANT]
> **Statistical Rule**: Standard Mann-Kendall must *never* be applied blindly to monthly or seasonal Earth-science series. Seasonal oscillations violate the independent-and-identically-distributed assumption.

For monthly or seasonal observations (period $m = 12$), the test is evaluated within each season independently across consecutive years:

$$S_{\text{total}} = \sum_{g=1}^m S_g, \quad \text{Var}(S_{\text{total}}) = \sum_{g=1}^m \text{Var}(S_g)$$

This isolates intra-annual seasonal variability from multi-year climate trajectory.

---

### 2.5 Serial Autocorrelation Correction (Hamed & Rao, 1998)
Positive serial autocorrelation in time series (e.g., persistent sea surface temperature anomalies) causes standard non-parametric tests to reject the null hypothesis too often.

TRIAGE applies the **Hamed & Rao (1998)** variance correction:
1. The series is first detrended using Sen's slope: $x^*_i = x_i - \beta_{\text{Sen}} \cdot t_i$.
2. Ranks $R_i$ of the detrended series are computed. Detrending is essential so that a true physical trend does not artificially manifest as serial correlation.
3. Significant rank autocorrelation coefficients $\rho_k$ (exceeding $\pm z_{1-\alpha/2}/\sqrt{n}$) are identified.
4. The variance of $S$ is scaled by the variance correction factor:

$$\frac{n}{n^*} = 1 + \frac{2}{n} \sum_{k=1}^{n-1} (n - k) \rho_k$$

$$\text{Var}^*(S) = \text{Var}(S) \cdot \frac{n}{n^*}$$

---

### 2.6 Spatial Multiplicity Control: Benjamini-Hochberg (FDR)
When testing $M$ spatial grid cells or sub-catchments simultaneously:
- Standard uncorrected $\alpha = 0.05$ guarantees that 5% of grid cells with *no real trend* will falsely register as "significant."
- TRIAGE controls the **False Discovery Rate (FDR)** via the Benjamini-Hochberg procedure:

$$P_{(k)} \le \frac{k}{M} \alpha$$

Controlling FDR preserves high statistical power while preventing map-wide hallucination of climate shifts.

---

### 2.7 Trend Direction & Practical Importance
A trend is classified into one of three states:
- **Increasing**: $\beta_{\text{Sen}} > 0$ **AND** $p < \alpha$.
- **Decreasing**: $\beta_{\text{Sen}} < 0$ **AND** $p < \alpha$.
- **No Trend**: $p \ge \alpha$ (even if $\beta_{\text{Sen}} \ne 0$).

> [!NOTE]
> **Statistical vs. Practical Significance**: A statistically significant trend with a negligible physical rate is explicitly annotated with a warning, distinguishing mathematical detectability from domain-level operational impact.

---

## 3. Benchmark Verification Suite (7 Canonical Cases)

The engine is validated against 7 synthetic benchmark series with analytically known ground truth:

| Case | Scenario | Description | Expected Outcome | Engine Performance |
|---|---|---|---|---|
| **1** | Clearly Increasing | $+0.08$ unit/step + Gaussian noise | `increasing`, $p < 0.05$, $\beta \approx 0.08$ | Verified (Passed) |
| **2** | Clearly Decreasing | $-0.07$ unit/step + Gaussian noise | `decreasing`, $p < 0.05$, $\beta \approx -0.07$ | Verified (Passed) |
| **3** | Stationary | Constant mean + Gaussian noise | `no trend`, $p \ge 0.05$ | Verified (Passed) |
| **4** | Seasonal (No Trend) | 12-month pure sinusoidal cycle | `no trend`, $p \ge 0.05$ (Seasonal MK) | Verified (Passed) |
| **5** | Seasonal (With Trend) | 12-month cycle $+ 0.05$ unit/step trend | `increasing`, $p < 0.05$ | Verified (Passed) |
| **6** | Missing Observations | 20% random NaNs in upward trend | $\approx 20\%$ missing, `increasing`, $p < 0.05$ | Verified (Passed) |
| **7** | Serial Autocorrelation | Stationary AR(1) process ($\phi = 0.6$) | $r_1 > 0.4$, $n/n^* > 1.0$, `no trend` | Verified (Passed) |

---

## 4. Software Architecture & API Endpoints

The trend engine is implemented in `trend_engine/` and is strictly decoupled from the UI and neural network components:

- **`trend_engine.api.analyze_variable()`**: Primary endpoint for single time series.
- **`trend_engine.api.compare_regions()`**: Comparative multi-region analysis with FDR adjustment.
- **`trend_engine.api.analyze_spatial_grid()`**: Gridded raster time series analysis with spatial false discovery rate correction.
- **`trend_engine.synthetic.generate_synthetic_datasets()`**: Reproducible test data generation.

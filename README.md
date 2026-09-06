# ColorChecker Calibration Pipeline

## 1. Define patch ROIs in HDR and PNG images

### Files

#### `save_physical_colorcheckerROI.py`

- PNG 이미지에서 ColorChecker 24개 패치의 ROI를 수동으로 선택
- ROI 좌표를 JSON으로 저장

#### `save_virtual_colorcheckerROI.py`
- HDR SceneColor 이미지에서 ColorChecker 24개 패치의 ROI를 수동으로 선택
- ROI 좌표를 JSON으로 저장


## 2. Convert PNG sRGB to CIE XYZ

### Files

#### `convert_PNG_sRGB_to_XYZ.py` (테스트용)
#### `iterate_converting_PNG_to_XYZ.py`

### Purpose
- PNG 이미지의 ColorChecker ROI에서 RGB 값을 추출한다.
- PNG의 sRGB 값을 linear sRGB로 변환한다.
- linear sRGB 값을 CIE XYZ 표준 색공간으로 변환한다.
- 각 ColorChecker 패치의 평균 XYZ 값을 CSV 파일로 저장한다.

### Input
- PNG image
- `colorchecker_calibration_result/physical_colorchecker/colorchecker_rois.json`

### Process
1. PNG 이미지를 OpenCV로 읽는다.
2. BGR 값을 RGB 순서로 변환한다.
3. 8-bit RGB 값을 `0~1` 범위로 변환한다.
4. inverse sRGB transfer function을 적용하여 linear sRGB로 변환한다.
5. 각 ROI의 평균 linear RGB 값을 계산한다.
6. linear sRGB → CIE XYZ 변환 행렬을 적용한다.

### Output
- ColorChecker 24개 패치의 CIE XYZ 값이 저장된 CSV 파일
- `colorchecker_calibration_result/physical_colorchecker/XYZ/`

Example:

| row | column | patch | X | Y | Z |
|---|---|---|---:|---:|---:|
| 1 | 1 | (1, 1) | ... | ... | ... |
| 1 | 2 | (1, 2) | ... | ... | ... |


## 3. Convert HDR SceneColor to CIE XYZ

### Files

#### `convert_HDR_linearRGB_to_XYZ.py` (테스트용)
#### `iterate_converting_HDR_to_XYZ.py`

### Purpose
- HDR 이미지의 ColorChecker ROI에서 SceneColor RGB 값을 추출한다.
- HDR SceneColor의 linear RGB 값을 CIE XYZ 표준 색공간으로 변환한다.
- 각 ColorChecker 패치의 평균 XYZ 값을 CSV 파일로 저장한다.

### Input
- HDR image
- `colorchecker_calibration_result/virtual_colorchecker/colorchecker_rois.json`

### Process
1. HDR 이미지를 OpenCV로 읽는다.
2. OpenCV의 BGR 값을 RGB 순서로 변환한다.
3. HDR SceneColor는 이미 linear RGB 값이므로 inverse sRGB transfer function을 적용하지 않는다.
4. 각 ROI의 평균 linear RGB 값을 계산한다.
5. linear sRGB / Rec.709 → CIE XYZ 변환 행렬을 적용한다.
6. 각 패치의 XYZ 값을 저장한다.

### Output
- ColorChecker 24개 패치의 CIE XYZ 값이 저장된 CSV 파일
- `colorchecker_calibration_result/virtual_colorchecker/XYZ/`

Example:

| row | column | patch | X | Y | Z |
|---|---|---|---:|---:|---:|
| 1 | 1 | (1, 1) | ... | ... | ... |
| 1 | 2 | (1, 2) | ... | ... | ... |

## 4. Calculate XYZ Error

### Files

#### `calculate_euclidean_error.py`

### Purpose
- Physical PNG와 virtual HDR에서 얻은 ColorChecker 패치별 CIE XYZ 값을 비교한다.
- 각 패치에 대해 XYZ 공간에서의 Euclidean distance를 계산한다.
- 24개 패치의 평균 XYZ error를 계산한다.
- 계산된 error를 CSV 파일로 저장한다.

### Input
- Physical ColorChecker XYZ CSV
- Virtual ColorChecker XYZ CSV

### Process
1. Physical XYZ CSV와 virtual XYZ CSV를 읽는다.
2. `row`, `column`, `patch`를 기준으로 같은 ColorChecker 패치끼리 매칭한다.
3. 각 패치에 대해 다음 Euclidean distance를 계산한다.

$$
e_i =
\sqrt{
(X_{physical}-X_{virtual})^2 +
(Y_{physical}-Y_{virtual})^2 +
(Z_{physical}-Z_{virtual})^2
}
$$

4. 24개 패치의 error 평균을 계산한다.

$$
E_{mean} =
\frac{1}{24}
\sum_{i=1}^{24} e_i
$$

5. 조명값별 mean XYZ error를 CSV 파일로 저장한다.

### Output
- Physical light와 virtual light 사이의 XYZ-domain error가 저장된 CSV 파일
- 예시: `colorchecker_calibration_result/error_result/virtual_R0G0B0_xyz.csv`

Example:

| virtual_light | physical_light | mean_xyz_error |
|---|---|---:|
| R0G0B0 | R0G0B0I255 | ... |
| R0G0B0 | R128G0B255I255 | ... |

## 5. Find the Optimal Physical-Virtual Light Pair

### Files

#### `output_top1_optimal_physical_light.py`
#### `output_top3_optimal_physical_light.py`

### Purpose
- 하나의 virtual light 조건에 대해 여러 physical light 후보와의 mean XYZ error를 비교한다.
- mean XYZ error가 가장 작은 physical light 조건을 찾는다.
- 각 virtual light에 대해 가장 잘 매칭되는 physical light 조건을 추출한다.
- 최적의 physical-virtual pair를 CSV 파일로 저장한다.

### Input
- 각 virtual light와 여러 physical light 조건의 비교 결과 CSV
- 예시: `R0G0B0I255.csv`
- 각 CSV에는 다음 정보가 포함된다.
  - `virtual_light`
  - `physical_light`
  - `mean_xyz_error`

### Process
1. 하나의 virtual light에 대해 계산된 physical light 후보들의 결과 CSV를 읽는다.
2. `mean_xyz_error`를 기준으로 오름차순 정렬한다.
3. 가장 작은 error를 가지는 physical light 조건을 선택한다.

$$
p^* = \arg\min_{p} E_{mean}(v,p)
$$

여기서

- $v$ : 고정된 virtual light 조건
- $p$ : physical light 후보
- $E_{mean}(v,p)$ : 24개 ColorChecker patch의 평균 XYZ error

4. 모든 virtual light 조건에 대해 같은 과정을 반복한다.
5. 각 virtual light에 대해 최적의 physical light 조건과 mean XYZ error를 하나의 CSV 파일에 저장한다.

### Output
- 각 virtual light에 대해 가장 작은 XYZ error를 가지는 physical light 조건이 저장된 CSV 파일
- `colorchecker_calibration_result/error_result/best_virtual_physical_pairs.csv`

Example:

| virtual_light | physical_light | mean_error |
|---------------|----------------|---:|
| R0G0B0        | R0G0B0I255     | ... |
| R0G0B0        | R85G0B0I255    | ... |
| R0G0B0        | R85G85B0I255   | ... |

## 6. Estimate the Calibration Matrix

### Files

#### `estimate_calibration_matrix.py`

### Purpose
- 최적의 physical-virtual RGB pair를 이용하여 두 조명 시스템 사이의 RGB 관계를 추정한다.
- Physical RGB를 입력으로 받아 대응하는 Virtual RGB를 예측하는 3×3 calibration matrix를 계산한다.
- 계산된 calibration matrix를 CSV 파일로 저장한다.

### Input
- `colorchecker_calibration_result/error_result/best_virtual_physical_pairs.csv`
- 각 행에는 다음 정보가 포함된다.
  - `virtual_light`
  - `physical_light`
  - `mean_error`

### Process
1. `virtual_light`와 `physical_light` 문자열에서 RGB 값을 추출한다.
2. 각 RGB 값을 열벡터 형태로 구성한다.(각 RGB 값은 0~255)

$$
\mathbf{p} = \begin{bmatrix} R_p \\ G_p \\ B_p \end{bmatrix} ,\qquad \mathbf{v} = \begin{bmatrix} R_v \\ G_v \\ B_v \end{bmatrix}
$$

4. Physical RGB와 Virtual RGB 사이의 관계를 다음과 같이 정의한다.

$$
\mathbf{v} = M\mathbf{p}
$$

여기서,

- $\mathbf{p}$ : physical light RGB
- $\mathbf{v}$ : virtual light RGB
- $M$ : 3×3 calibration matrix

5. 여러 physical-virtual RGB pair를 이용하여 least-squares 방식으로 calibration matrix를 추정한다.

$$
M = V P^{+}
$$

여기서,

- $P$ : physical RGB sample matrix
- $V$ : virtual RGB sample matrix
- $P^{+}$ : $P$의 pseudo inverse

6. 추정된 calibration matrix를 CSV 파일로 저장한다.

### Output
- 3×3 calibration matrix가 저장된 CSV 파일
- `colorchecker_calibration_result/error_result/calibration_matrix.csv`

Example:

|  | R_physical | G_physical | B_physical |
|---|---:|---:|---:|
| R_virtual | ... | ... | ... |
| G_virtual | ... | ... | ... |
| B_virtual | ... | ... | ... |

## 7. Validate the Calibration Matrix

### Files

#### `validate_calibration_matrix.py`
#### `colorchecker_calibration_result/test/compare_calibrated_virtual_error.py`

### Purpose
- Calibration matrix를 만들 때 사용하지 않은 새로운 RGB 조건으로 calibration 결과를 검증한다.
- 주어진 virtual light RGB에 대응하는 physical light RGB를 calibration matrix를 이용해 계산한다.
- 예측된 physical light 조건으로 실제 촬영을 수행한 뒤, virtual result와의 XYZ error를 계산한다.

### Input
- Calibration matrix CSV
- Validation용 virtual light RGB
- Calibration에 사용하지 않은 validation image / XYZ CSV

### Process
1. Validation에 사용할 virtual light RGB를 선택한다.
2. Calibration 단계에서 정의한 관계는 다음과 같다.

$$
\mathbf{v} = M\mathbf{p}
$$

여기서,

- $\mathbf{v}$ : virtual light RGB
- $\mathbf{p}$ : physical light RGB
- $M$ : calibration matrix

3. 주어진 virtual RGB에 대응하는 physical RGB를 구하기 위해 calibration matrix의 pseudoinverse를 사용한다.

$$
\mathbf{p} = M^{+}\mathbf{v}
$$

4. 계산된 physical RGB 조건으로 실제 조명을 제어하고 ColorChecker 이미지를 촬영한다.
5. Physical PNG와 virtual HDR에서 ColorChecker 24개 패치의 CIE XYZ 값을 계산한다.
6. 각 패치의 XYZ Euclidean distance를 계산하고, 24개 패치의 평균 error를 구한다.

$$
e_i = \sqrt{(X_{physical}-X_{virtual})^2 + (Y_{physical}-Y_{virtual})^2 + (Z_{physical}-Z_{virtual})^2}
$$

$$
E_{mean} = \frac{1}{24} \sum_{i=1}^{24} e_i
$$

### Output
- Validation condition별 calibrated XYZ error
- Calibration matrix로 계산된 physical RGB
- Baseline과 비교 가능한 mean XYZ error 결과
- `colorchecker_calibration_result/test/calibrated`

Example:

| virtual_light | calibrated_physical_light | mean_xyz_error |
|---------------|---------------------------|---:|
| R43G128B213   | R...G...B...              | ... |

## 8. Compare Baseline and Calibrated Results

### Files

#### `colorchecker_calibration_result/test/compare_baseline_virtual_error.py`
#### `colorchecker_calibration_result/test/compare_baseline_calibrated_error.py`

### Purpose
- Calibration matrix를 적용하지 않은 baseline 결과와 calibration matrix를 적용한 결과를 비교한다.
- 각 validation virtual light 조건에 대해 mean XYZ error가 얼마나 감소했는지 계산한다.
- Calibration 적용 후의 improvement를 정량적으로 평가한다.

### Input
- Baseline result CSV `colorchecker_calibration_result/test/baseline/XYZ/`
- Calibrated result CSV `colorchecker_calibration_result/test/calibrated/XYZ/`

각 CSV에는 다음 정보가 포함된다.
- `virtual_light`
- `physical_light`
- `mean_xyz_error`

### Process
1. Baseline result CSV와 calibrated result CSV를 읽는다.
2. `virtual_light`를 기준으로 같은 validation condition끼리 매칭한다.
3. 각 virtual light 조건에 대해 다음 값을 비교한다.

- Baseline mean XYZ error

$$
E_{baseline}
$$

- Calibrated mean XYZ error

$$
E_{calibrated}
$$

4. Calibration 적용에 따른 improvement를 다음과 같이 계산한다.

$$
\mathrm{Improvement} (\\%) = \frac{E_{baseline} - E_{calibrated}}{E_{baseline}} \times 100
$$


5. Improvement가 양수이면 calibration 적용 후 XYZ error가 감소한 것을 의미한다.
6. 모든 validation condition에 대해 baseline error, calibrated error, improvement를 하나의 CSV 파일에 저장한다.
7. 전체 validation condition의 평균 improvement를 계산하여 calibration 성능을 요약한다.

### Output
- Baseline과 calibrated result의 비교 결과가 저장된 CSV 파일

Example:

| virtual_light | baseline_error | calibrated_error | improvement |
|---|---:|---:|---:|
| R43G43B43 | ... | ... | ... |
| R96G160B32 | ... | ... | ... |

### Evaluation
- `calibrated_error < baseline_error`이면 calibration에 의해 matching error가 감소한 것으로 평가한다.
- 여러 validation condition에 대해 평균 improvement를 계산하여 전체적인 calibration 효과를 확인한다.

$$
\overline{\mathrm{Improvement}} = \frac{1}{N} \sum_{i=1}^{N} \mathrm{Improvement}_i
$$

23.16127786146579% 더 나아진 것을 확인했다.

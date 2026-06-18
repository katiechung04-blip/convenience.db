# 편의점 데이터베이스 관리 시스템 (Convenience Store DB System)

[cite_start]본 프로젝트는 편의점 유통 환경에서 발생하는 판매, 재고, 발주, 상품/공급업체, 고객 정보를 유기적으로 관리하고 통계를 분석할 수 있는 SQLite 기반의 CLI 인터페이스 시스템입니다. [cite: 14, 15, 20]

## 1. 폴더 구조 및 파일 위치 (Directory Structure)
[cite_start]명세서 요구사항에 맞춰 최상위 디렉토리에 README 파일을 배치하였습니다. [cite: 73]
.
[cite_start]├── README.md               <- 시스템 설명 및 실행 가이드 (최상위 디렉토리 위치) [cite: 73]
[cite_start]├── ERD_설명문서.pdf         <- ERD 및 엔티티/관계 명세서 (클라우드 다운로드 링크 포함) [cite: 66, 69]
└── src/                    <- 구현 소스 코드 디렉토리
    [cite_start]└── main.py             <- 역할 기반 7대 메뉴 CLI 인터페이스 메인 코드 [cite: 71, 72]

## 2. 데이터베이스 구성 및 클라우드 안내
- [cite_start]과제 요건에 의거하여 실제 데이터 파일(`convenience.db`)은 제출물 압축본에 포함하지 않았습니다. [cite: 68]
- [cite_start]전체 데이터가 적재된 원본 데이터베이스 파일은 'ERD_설명문서.pdf' 내에 명시된 구글 드라이브 공유 링크를 통해 다운로드하실 수 있습니다. [cite: 69]

## 3. 인터페이스 실행 방법 (How to Run)
[cite_start]본 프로그램은 파이썬 내장 라이브러리만을 사용하여 개발되었으므로 즉시 실행 가능합니다. [cite: 72] [cite_start]압축을 해제한 후 터미널에서 아래 명령어로 메인 인터페이스를 구동해 주십시오. [cite: 74]

```bash
python src/main.py

生成allure报告

allure generate ./allure-results -o ./allure-report --clean

打开allure报告

allure open ./allure-report

清除allure报告

**# 如果存在allure-results目录，删除它**
**rm** -rf allure-results/

**# 如果存在allure-report目录，删除它**
**rm** -rf allure-report/

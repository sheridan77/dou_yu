import os

from codecs import open

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# 打包哪些文件夹
packages = ['douyu_api']
# 安装依赖包
requires = ['requests>=2.26.0', 'websocket-client', "pystt", "PyExecJS"]
# 测试依赖包
test_requirements = []
# 读取about信息
about = {}
with open(os.path.join(here, 'douyu_api', '__version__.py'), 'r', 'utf-8') as f:
    exec(f.read(), about)

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=packages,
    # package_data={'': ['LICENSE', 'NOTICE']},
    package_dir={'twitter-api': 'twitter_api'},
    include_package_data=True,
    python_requires=">=3.7.0",
    install_requires=requires,
    license=about['__license__'],
    zip_safe=False,
    tests_require=test_requirements,
    project_urls={
        # 'Documentation': 'https://git.blackmirrors.tech:19443/ldw123/twitter-api',
        'Source': 'https://git.blackmirrors.tech:19443/ldw123/douyu-api',
    },
)

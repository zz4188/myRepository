"""
TicketMaster 安装脚本
用于安装和配置应用程序
"""

from setuptools import setup, find_packages
import os

# 读取 README.md
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# 读取 requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name='TicketMaster',
    version='1.0.0',
    author='TicketMaster Team',
    author_email='support@ticketmaster.com',
    description='Windows 抢票软件 - 支持 12306、大麦网、携程',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/TicketMaster',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Internet',
        'Topic :: Utilities',
    ],
    python_requires='>=3.10',
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'ticketmaster=main:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

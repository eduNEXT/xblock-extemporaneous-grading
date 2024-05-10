FROM openedx/xblock-sdk
RUN mkdir -p /usr/local/src/xblock-extemporaneous-grading
VOLUME ["/usr/local/src/xblock-extemporaneous-grading"]
RUN apt-get update && apt-get install -y gettext
RUN echo "pip install -r /usr/local/src/xblock-extemporaneous-grading/requirements.txt" >> /usr/local/src/xblock-sdk/install_and_run_xblock.sh
RUN echo "pip install -e /usr/local/src/xblock-extemporaneous-grading" >> /usr/local/src/xblock-sdk/install_and_run_xblock.sh
RUN echo "cd /usr/local/src/xblock-extemporaneous-grading && make compile_translations && cd /usr/local/src/xblock-sdk" >> /usr/local/src/xblock-sdk/install_and_run_xblock.sh
RUN echo "exec python /usr/local/src/xblock-sdk/manage.py \"\$@\"" >> /usr/local/src/xblock-sdk/install_and_run_xblock.sh
RUN chmod +x /usr/local/src/xblock-sdk/install_and_run_xblock.sh
ENTRYPOINT ["/bin/bash", "/usr/local/src/xblock-sdk/install_and_run_xblock.sh"]
CMD ["runserver", "0.0.0.0:8000"]

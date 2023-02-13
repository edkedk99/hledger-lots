remote_server := phl
remote_wheel_dir=/shared/wheels

get_value = $(shell sed -n "s/\($1 \?= \?\)\(.*\)/\2/p" setup.cfg)
pkg_name := $(call get_value,name)
version := $(call get_value,version)
wheel := $(pkg_name)-$(version)-py3-none-any.whl

.PHONY: local
local:
	make build && \
	pip3 uninstall -y $(pkg_name) && \
	pip3 install dist/$(wheel)


.PHONY: build
build:
	make fix && python -m build



.PHONY: fix
fix:
	source venv/bin/activate && \
	pyright $(pkg_name) && \
	pycln $(pkg_name) && \
	isort --profile black $(pkg_name) && \
	black $(pkg_name)





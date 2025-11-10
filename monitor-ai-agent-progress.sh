while (true) ; do echo "temp $(ls -ltr /tmp/ | wc -l)" | tee >(say) ; sleep 2 ; echo "diff: $(git diff | cat | wc -l)" | tee >(say) ; date ; sleep 60 ; done

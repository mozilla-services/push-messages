<a name="0.5"></a>
## 0.5 (2016-04-11)


#### Features

*   return 404 for no registered key, and refactor for redis only ([959d20a6](https://github.com/mozilla-services/push-messages/commit/959d20a61b09a6e7272923feecd42b156fd987cd), closes [#6](https://github.com/mozilla-services/push-messages/issues/6))



<a name="0.4"></a>
## 0.4 (2016-04-08)


#### Bug Fixes

*   coerce message values to ensure validation passes ([01c5d40b](https://github.com/mozilla-services/push-messages/commit/01c5d40b4cf06e1ff97773ac26b6e3e86effe799))



<a name="0.3"></a>
## 0.3 (2016-04-07)


#### Bug Fixes

*   use floats for e-notation value ([47327494](https://github.com/mozilla-services/push-messages/commit/47327494d63505cc689174c2c9232a21828e4a2c))



<a name="0.2"></a>
## 0.2 (2016-04-07)


#### Bug Fixes

*   timestamp should be a integer ([b7ed0448](https://github.com/mozilla-services/push-messages/commit/b7ed04488ad0d0a799c3596d7081ee87443d15f3))



<a name="0.1"></a>
## 0.1 (2016-04-06)


#### Bug Fixes

*   restrict scan to avoid tests import ([03991fd7](https://github.com/mozilla-services/push-messages/commit/03991fd77ef92b9a6a22515c2afde0afe79ca8f9))

#### Test

*   add full test suite for unit tests and wsgi app ([8a6bad72](https://github.com/mozilla-services/push-messages/commit/8a6bad726a95bf5ee4647806f2566a4b1156bbec))

#### Chore

*   add clog toml for changelog gen ([d93b3db1](https://github.com/mozilla-services/push-messages/commit/d93b3db164c227f7fa1d51efdd0021424d10e458))
*   add initial project files and project base ([5c048d32](https://github.com/mozilla-services/push-messages/commit/5c048d32cc4fd2ca97d38a473700fc85f591513d))

#### Doc

*   add architecture background ([ce98cd98](https://github.com/mozilla-services/push-messages/commit/ce98cd98398c49077b522b6d81769fd601773cc9))

#### Features

*   add dockerized building per Dockerflow specs ([3728713f](https://github.com/mozilla-services/push-messages/commit/3728713fafa6e7d78963be658215f460d3ae0259), closes [#8](https://github.com/mozilla-services/push-messages/issues/8))
*   initial working push messages api ([691386b4](https://github.com/mozilla-services/push-messages/commit/691386b42d034ad6513dedb2f81d3a35548caaf7))
